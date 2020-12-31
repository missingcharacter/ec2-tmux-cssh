#!/usr/bin/env python3
from botocore.client import BaseClient
from collections.abc import ValuesView
from pathlib import Path
from subprocess import run


def get_all_ec2_instances(client_ec2: BaseClient):
    return [
        host
        for page in client_ec2.get_paginator("describe_instances").paginate()
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


def get_all_ips(ec2_list: list[dict], key: str, value: str) -> list[str]:
    hosts = get_hosts_with_key_value(ec2_list=ec2_list, key=key, value=value)
    return [ip for host in hosts for ip in ips_in_instance(host)]


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
