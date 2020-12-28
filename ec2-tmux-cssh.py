#!/usr/bin/env python3
import boto3
import inquirer

from utils import get_all_ec2_instances, get_all_ips, get_bastions, get_running, get_unique_tags, get_user_ssh_keys
from subprocess import run

known_ssh_users = sorted(["ubuntu", "ec2-user", "centos", "admin", "core", "fedora", "root", "bitnami"])
ec2_client = boto3.client("ec2")
ec2_instances = get_all_ec2_instances(client_ec2=ec2_client)
running_instances = get_running(ec2_list=ec2_instances)
unique_tags = get_unique_tags(ec2_list=running_instances)
sorted_tag_keys = sorted(unique_tags.keys())

hosts_tag_key = inquirer.prompt(
    [inquirer.List("answer", message="What tag_key should I use to find instances?", choices=sorted_tag_keys)]
)

hosts_tag_value = inquirer.prompt(
    [
        inquirer.List(
            "answer",
            message=f"What {hosts_tag_key['answer']} value should I use to find instances?",
            choices=sorted(unique_tags[hosts_tag_key["answer"]]),
        )
    ]
)

ips_to_ssh = get_all_ips(ec2_list=running_instances, key=hosts_tag_key["answer"], value=hosts_tag_value["answer"])

sorted_ssh_keys = sorted(get_user_ssh_keys())
hosts_ssh_questions = [
    inquirer.List("ssh_key", message="Which private key should I use for the hosts?", choices=sorted_ssh_keys),
    inquirer.List("user", message="Which ssh user should I use for the hosts?", choices=known_ssh_users),
]
hosts_ssh_params = inquirer.prompt(hosts_ssh_questions)
tmux_cssh_args = ["tmux-cssh", "-u", hosts_ssh_params["user"], "-i", hosts_ssh_params["ssh_key"]]

# bastion questions
proxy_bastion = inquirer.prompt(
    [inquirer.Confirm("answer", message="Will you proxy through a bastion host?", default=True)]
)
if proxy_bastion["answer"]:
    bastions_tag_key = inquirer.prompt(
        [inquirer.List("answer", message="What tag_key should I use to find bastions?", choices=sorted_tag_keys)]
    )

    bastions_tag_value = inquirer.prompt(
        [
            inquirer.List(
                "answer",
                message=f"What {bastions_tag_key['answer']} value should I use to find bastions?",
                choices=sorted(unique_tags[bastions_tag_key["answer"]]),
            )
        ]
    )
    bastions = get_bastions(
        ec2_list=running_instances, key=bastions_tag_key["answer"], value=bastions_tag_value["answer"]
    )
    bastions_ssh_questions = [
        inquirer.List("name", message="Which bastion should I proxy through?", choices=sorted(bastions.keys())),
        inquirer.List(
            "ssh_key", message="Which private key should I use for the bastion host?", choices=sorted_ssh_keys
        ),
        inquirer.List("user", message="Which ssh user should I user for the bastion host?", choices=known_ssh_users),
    ]
    bastions_ssh_params = inquirer.prompt(bastions_ssh_questions)

    proxy_command = " ".join(
        [
            "ssh",
            "-i",
            bastions_ssh_params["ssh_key"],
            f"{bastions_ssh_params['user']}@{bastions[bastions_ssh_params['name']]}",
            "-W %h:%p",
        ]
    )
    tmux_cssh_args += ["-sa", f"\"-o ProxyCommand='{proxy_command}'\""]

tmux_cssh_command = " ".join(tmux_cssh_args)
run(args=f"{tmux_cssh_command} {' '.join(ips_to_ssh)}", shell=True)
