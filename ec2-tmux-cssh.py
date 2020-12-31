#!/usr/bin/env python3
import boto3
import click
import inquirer

from typing import Optional
from utils import get_all_ec2_instances, get_all_ips, get_bastions, get_running, get_unique_tags, get_user_ssh_keys
from subprocess import run


@click.command()
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
) -> None:
    known_ssh_users = sorted(["ubuntu", "ec2-user", "centos", "admin", "core", "fedora", "root", "bitnami"])
    ec2_client = boto3.client("ec2")
    ec2_instances = get_all_ec2_instances(client_ec2=ec2_client)
    running_instances = get_running(ec2_list=ec2_instances)
    unique_tags = get_unique_tags(ec2_list=running_instances)
    sorted_tag_keys = sorted(unique_tags.keys())

    if hosts_tag_key is None:
        hosts_tag_key = inquirer.list_input(
            message="What tag_key should I use to find instances?", choices=sorted_tag_keys
        )

    if hosts_tag_value is None:
        hosts_tag_value = inquirer.list_input(
            message=f"What {hosts_tag_key} value should I use to find instances?",
            choices=sorted(unique_tags[hosts_tag_key]),
        )

    ips_to_ssh = get_all_ips(ec2_list=running_instances, key=hosts_tag_key, value=hosts_tag_value)
    ssh_keys = get_user_ssh_keys()

    if hosts_ssh_key is None:
        hosts_ssh_key = inquirer.list_input(message="Which private key should I use for the hosts?", choices=ssh_keys)

    if hosts_user is None:
        hosts_user = inquirer.list_input(message="Which ssh user should I use for the hosts?", choices=known_ssh_users)

    tmux_cssh_args = ["tmux-cssh", "-u", hosts_user, "-i", hosts_ssh_key]

    # bastion questions
    if use_bastion:
        if bastions_tag_key is None:
            bastions_tag_key = inquirer.list_input(
                message="What tag_key should I use to find bastions?", choices=sorted_tag_keys
            )

        if bastions_tag_value is None:
            bastions_tag_value = inquirer.list_input(
                message=f"What {bastions_tag_key} value should I use to find bastions?",
                choices=sorted(unique_tags[bastions_tag_key]),
            )

        bastions = get_bastions(ec2_list=running_instances, key=bastions_tag_key, value=bastions_tag_value)

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
                message="Which ssh user should I user for the bastion host?", choices=known_ssh_users
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
        tmux_cssh_args += ["-sa", f"\"-o ProxyCommand='{proxy_command}'\""]

    tmux_cssh_command = " ".join(tmux_cssh_args)
    run(args=f"{tmux_cssh_command} {' '.join(ips_to_ssh)}", shell=True)


if __name__ == "__main__":
    main()
