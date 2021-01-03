#!/usr/bin/env python3
import click
import inquirer

from typing import Optional
from utils import (
    get_all_ec2_ips,
    get_all_ecs_ips,
    get_basics,
    get_user_ssh_keys,
    tmux_use_bastion
)
from subprocess import run


@click.command()
@click.option("--is-ecs", is_flag=True, default=False, help="Find ec2 instances where ecs service runs on")
@click.option("--ecs-cluster", help="ECS Cluster where ECS Service runs on")
@click.option("--ecs-service", help="ECS Service we want to find EC2 instances for")
@click.option("--hosts-tag-key", help="Tag key to find hosts with")
@click.option("--hosts-tag-value", help="Tag value to find hosts with")
@click.option("--hosts-ssh-key", help="SSH Private Key for hosts")
@click.option("--hosts-user", help="SSH user for hosts")
@click.option("--use-bastion", is_flag=True, default=False, help="Proxy SSH through a bastion host")
@click.option("--bastions-tag-key", help="Tag key to find bastions with")
@click.option("--bastions-tag-value", help="Tag value to find bastions with")
@click.option("--bastion-name", help="Bastion EC2 Name")
@click.option("--bastion-ssh-key", help="SSH Private Key for bastion")
@click.option("--bastion-user", help="SSH user for bastion")
def main(
    is_ecs: bool = False,
    use_bastion: bool = False,
    hosts_tag_key: Optional[str] = None,
    hosts_tag_value: Optional[str] = None,
    hosts_ssh_key: Optional[str] = None,
    hosts_user: Optional[str] = None,
    bastions_tag_key: Optional[str] = None,
    bastions_tag_value: Optional[str] = None,
    bastion_name: Optional[str] = None,
    bastion_ssh_key: Optional[str] = None,
    bastion_user: Optional[str] = None,
    ecs_cluster: Optional[str] = None,
    ecs_service: Optional[str] = None
) -> None:
    ec2_client, ssh_users, running_instances, unique_tags, sorted_tag_keys = get_basics()

    if is_ecs:
        ips_to_ssh = get_all_ecs_ips(ec2_client=ec2_client, ecs_cluster=ecs_cluster, ecs_service=ecs_service)
    else:
        ips_to_ssh = get_all_ec2_ips(
            ec2_list=running_instances,
            hosts_tag_key=hosts_tag_key,
            hosts_tag_value=hosts_tag_value,
            tag_keys=sorted_tag_keys,
            unique_tags=unique_tags
        )

    ssh_keys = get_user_ssh_keys()

    if hosts_ssh_key is None:
        hosts_ssh_key = inquirer.list_input(message="Which private key should I use for the hosts?", choices=ssh_keys)

    if hosts_user is None:
        hosts_user = inquirer.list_input(message="Which ssh user should I use for the hosts?", choices=ssh_users)

    tmux_cssh_args = ["tmux-cssh", "-u", hosts_user, "-i", hosts_ssh_key]

    # bastion questions
    if use_bastion:
        tmux_cssh_args += tmux_use_bastion(
            tag_keys=sorted_tag_keys,
            ssh_keys=ssh_keys,
            ssh_users=ssh_users,
            unique_tags=unique_tags,
            instances_running=running_instances,
            bastions_tag_key=bastions_tag_key,
            bastions_tag_value=bastions_tag_value,
            bastion_name=bastion_name,
            bastion_ssh_key=bastion_ssh_key,
            bastion_user=bastion_user
        )

    tmux_cssh_command = " ".join(tmux_cssh_args)
    run(args=f"{tmux_cssh_command} {' '.join(ips_to_ssh)}", shell=True)


if __name__ == "__main__":
    main()
