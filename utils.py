#!/usr/bin/env python3
import boto3
import inquirer

from botocore.client import BaseClient
from collections.abc import ValuesView
from pathlib import Path
from subprocess import run
from typing import Optional


def get_basics() -> (BaseClient, list[str], list[dict], list[set], list[str]):
    known_ssh_users = sorted(["ubuntu", "ec2-user", "centos", "admin", "core", "fedora", "root", "bitnami"])
    ec2_client = boto3.client("ec2")
    ec2_instances = get_all_ec2_instances(client_ec2=ec2_client)
    running_instances = get_running(ec2_list=ec2_instances)
    unique_tags = get_unique_tags(ec2_list=running_instances)
    sorted_tag_keys = sorted(unique_tags.keys())
    return ec2_client, known_ssh_users, running_instances, unique_tags, sorted_tag_keys


def get_all_ec2_instances(client_ec2: BaseClient, ec2_ids: Optional[list[str]] = None) -> list[dict]:
    kwargs = dict()
    if ec2_ids:
        kwargs["InstanceIds"] = ec2_ids
    return [
        host
        for page in client_ec2.get_paginator("describe_instances").paginate(**kwargs)
        for reservations in page["Reservations"]
        for host in reservations["Instances"]
    ]


def get_running(ec2_list: list[dict]) -> list[dict]:
    return [host for host in ec2_list if host.get("State", {}).get("Name", "") == "running"]


def get_unique_tags(ec2_list: list[dict]) -> dict:
    tags = {}
    for host in ec2_list:
        for tag in host["Tags"]:
            if tag["Key"] in tags.keys():
                tags[tag["Key"]].add(tag["Value"])
            else:
                tags[tag["Key"]] = {tag["Value"]}
    return tags


def get_tags_as_dict(tags_list: list[dict]) -> dict:
    return {element["Key"]: element["Value"] for element in tags_list}


def is_key_value_in_instance(instance: dict, key: str, value: str) -> bool:
    tags = get_tags_as_dict(instance["Tags"])
    if tags.get(key) == value:
        return True
    else:
        return False


def get_hosts_with_key_value(ec2_list: list[dict], key: str, value: str) -> ValuesView:
    hosts = {
        index: host
        for index, host in enumerate(ec2_list)
        if is_key_value_in_instance(instance=host, key=key, value=value)
    }
    [ec2_list.pop(index) for index in sorted(hosts.keys(), reverse=True)]
    return hosts.values()


def ips_in_instance(instance: dict) -> list[str]:
    return [
        ip["PrivateIpAddress"] for interface in instance["NetworkInterfaces"] for ip in interface["PrivateIpAddresses"]
    ]


def get_bastion(instance: dict) -> dict:
    tags = get_tags_as_dict(instance["Tags"])
    return {tags["Name"]: instance["PublicIpAddress"]}


def get_bastions(ec2_list: list[dict], key: str, value: str) -> dict:
    hosts = get_hosts_with_key_value(ec2_list=ec2_list, key=key, value=value)
    return {k: v for host in hosts for k, v in get_bastion(host).items()}


def all_ips_in_all_hosts(hosts: list[dict]) -> list[str]:
    return [ip for host in hosts for ip in ips_in_instance(host)]


def get_all_ec2_ips(
    ec2_list: list[dict], hosts_tag_key: str, hosts_tag_value: str, tag_keys: list[str], unique_tags: dict
) -> list[str]:
    if hosts_tag_key is None:
        hosts_tag_key = inquirer.list_input(message="What tag_key should I use to find instances?", choices=tag_keys)

    if hosts_tag_value is None:
        hosts_tag_value = inquirer.list_input(
            message=f"What {hosts_tag_key} value should I use to find instances?",
            choices=sorted(unique_tags[hosts_tag_key]),
        )

    ec2_hosts = list(get_hosts_with_key_value(ec2_list=ec2_list, key=hosts_tag_key, value=hosts_tag_value))
    return all_ips_in_all_hosts(hosts=ec2_hosts)


def get_user_ssh_keys() -> list[str]:
    home_dir = Path.home()
    ssh_dir = home_dir / ".ssh"
    return sorted(
        [
            ssh_key.__str__()
            for ssh_key in ssh_dir.iterdir()
            if run(args=f"file {ssh_key.__str__()}", shell=True, capture_output=True).stdout.endswith(b"private key\n")
        ]
    )


def tmux_use_bastion(
    tag_keys: list[str],
    ssh_keys: list[str],
    ssh_users: list[str],
    unique_tags: dict,
    instances_running: list[dict],
    bastions_tag_key: Optional[str] = None,
    bastions_tag_value: Optional[str] = None,
    bastion_name: Optional[str] = None,
    bastion_ssh_key: Optional[str] = None,
    bastion_user: Optional[str] = None,
) -> list[str]:
    if bastions_tag_key is None:
        bastions_tag_key = inquirer.list_input(message="What tag_key should I use to find bastions?", choices=tag_keys)

    if bastions_tag_value is None:
        bastions_tag_value = inquirer.list_input(
            message=f"What {bastions_tag_key} value should I use to find bastions?",
            choices=sorted(unique_tags[bastions_tag_key]),
        )

    bastions = get_bastions(ec2_list=instances_running, key=bastions_tag_key, value=bastions_tag_value)

    if bastion_name is None:
        bastion_name = inquirer.list_input(
            message="Which bastion should I proxy through?", choices=sorted(bastions.keys())
        )

    if bastion_ssh_key is None:
        bastion_ssh_key = inquirer.list_input(
            message="Which private key should I use for the bastion host?", choices=ssh_keys
        )

    if bastion_user is None:
        bastion_user = inquirer.list_input(
            message="Which ssh user should I user for the bastion host?", choices=ssh_users
        )

    proxy_command = " ".join(
        [
            "ssh",
            "-i",
            bastion_ssh_key,
            f"{bastion_user}@{bastions[bastion_name]}",
            "-W %h:%p",
        ]
    )
    return ["-sa", f"\"-o ProxyCommand='{proxy_command}'\""]


def get_all_ecs_clusters(client_ecs: BaseClient) -> list[str]:
    return sorted(
        [cluster for page in client_ecs.get_paginator("list_clusters").paginate() for cluster in page["clusterArns"]]
    )


def get_all_ecs_services_of_type(
    client_ecs: BaseClient, cluster_arn: str, launch_type: str, scheduling_strategy: str
) -> list:
    return [
        service
        for page in client_ecs.get_paginator("list_services").paginate(
            cluster=cluster_arn, launchType=launch_type, schedulingStrategy=scheduling_strategy
        )
        for service in page.get("serviceArns", [])
    ]


def get_all_services_in_ecs_cluster(client_ecs: BaseClient, cluster_arn: str) -> list[str]:
    services: list = get_all_ecs_services_of_type(
        client_ecs=client_ecs, cluster_arn=cluster_arn, launch_type="EC2", scheduling_strategy="REPLICA"
    )
    services += get_all_ecs_services_of_type(
        client_ecs=client_ecs, cluster_arn=cluster_arn, launch_type="EC2", scheduling_strategy="DAEMON"
    )
    return sorted(services)


def get_ec2_where_service(client_ecs: BaseClient, cluster_arn: str, service: str) -> list[str]:
    task_arns = {
        task
        for page in client_ecs.get_paginator("list_tasks").paginate(cluster=cluster_arn, serviceName=service)
        for task in page["taskArns"]
    }

    if task_arns:
        container_instances = {
            task["containerInstanceArn"]
            for task in client_ecs.describe_tasks(cluster=cluster_arn, tasks=list(task_arns))["tasks"]
        }
    else:
        raise Exception("No container instances were found")

    return list(
        {
            instance["ec2InstanceId"]
            for instance in client_ecs.describe_container_instances(
                cluster=cluster_arn, containerInstances=list(container_instances)
            )["containerInstances"]
        }
    )


def get_all_ecs_ips(
    ec2_client: BaseClient, ecs_cluster: Optional[str] = None, ecs_service: Optional[str] = None
) -> list[str]:
    ecs_client = boto3.client("ecs")
    if ecs_cluster is None:
        ecs_cluster = inquirer.list_input(
            message="What ECS Cluster do you want to look services for?",
            choices=get_all_ecs_clusters(client_ecs=ecs_client),
        )

    if ecs_service is None:
        ecs_service = inquirer.list_input(
            message="What ECS Service do you want to find EC2 instances for?",
            choices=get_all_services_in_ecs_cluster(client_ecs=ecs_client, cluster_arn=ecs_cluster),
        )

    ec2_instance_ids = get_ec2_where_service(client_ecs=ecs_client, cluster_arn=ecs_cluster, service=ecs_service)
    ec2_hosts = get_all_ec2_instances(client_ec2=ec2_client, ec2_ids=ec2_instance_ids)
    return all_ips_in_all_hosts(hosts=ec2_hosts)
