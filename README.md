# ec2-tmux-cssh

## Overview

tmux cluster ssh to multiple ec2 instances

## Requirements

- AWS access
  - EC2 only to [DescribeInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html)
  - ECS functionality requires:
    - [DescribeInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html)
    - [ListClusters](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ListClusters.html)
    - [ListServices](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ListServices.html)
    - [ListTasks](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ListTasks.html)
    - [DescribeTasks](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DescribeTasks.html)
    - [DescribeContainerInstances](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DescribeContainerInstances.html)
- Private ssh keys for the servers you will try to connect to in `~/.ssh`
- [file](https://man7.org/linux/man-pages/man1/file.1.html) in your `${PATH}`
- [tmux-cssh](https://github.com/zinic/tmux-cssh/blob/042fdec2dc51bcfe62499e72f589dc9c146ab71a/tmux-cssh) in your `${PATH}`
  - [tmux](https://github.com/tmux/tmux/wiki) in your `${PATH}`
  - [ssh](https://www.openssh.com/) in your `${PATH}`
- [poetry](https://github.com/python-poetry/poetry)

## Before first run

1. `poetry install`

## How to use

### Example: Only providing use bastion option

```
$ cd /path/to/this/repository
$ AWS_PROFILE=my-aws-profile poetry run python ./ec2-tmux-cssh.py --use-bastion
[?] What tag_key should I use to find instances?: Name
 > Name
   Role
   aws:autoscaling:groupName
   aws:cloudformation:logical-id
   aws:cloudformation:stack-id
   aws:cloudformation:stack-name
   aws:ec2launchtemplate:id
   aws:ec2launchtemplate:version

[?] What Name value should I use to find instances?: qa-ecs-cluster
 > qa-ecs-cluster
   rabbitmq
   ecs-cluster

[?] Which private key should I use for the hosts?: /Users/macuser/.ssh/qa.pem
 + README
   /Users/macuser/.ssh/id_ed25519
   /Users/macuser/.ssh/prod-bastion.pem
   /Users/macuser/.ssh/prod.pem
   /Users/macuser/.ssh/qa-bastion.pem
 > /Users/macuser/.ssh/qa.pem

[?] Which ssh user should I use for the hosts?: ec2-user
   centos
 > ec2-user
   ubuntu

[?] What tag_key should I use to find bastions?: Role
   Name
 > Role
   aws:autoscaling:groupName
   aws:cloudformation:logical-id
   aws:cloudformation:stack-id
   aws:cloudformation:stack-name
   aws:ec2launchtemplate:id
   aws:ec2launchtemplate:version

[?] What Role value should I use to find bastions?: bastion
   DB
 > bastion

[?] Which bastion should I proxy through?: qa-bastion
   prod-bastion
 > qa-bastion
   stage-bastion

[?] Which private key should I use for the bastion host?: /Users/macuser/.ssh/qa-bastion.pem
   /Users/macuser/.ssh/id_ed25519
   /Users/macuser/.ssh/prod-bastion.pem
   /Users/macuser/.ssh/prod.pem
 > /Users/macuser/.ssh/qa-bastion.pem
   /Users/macuser/.ssh/qa.pem

[?] Which ssh user should I user for the bastion host?: ubuntu
   centos
   ec2-user
 > ubuntu

I will tmux-cssh through bastion qa-bastion to these IPs: ['10.10.21.104', '10.10.21.230', '10.10.21.223', '10.10.20.118', '10.10.20.83', '10.10.20.39']
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.21.104'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.21.230'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.21.223'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.20.118'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.20.83'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.20.39'
[exited]
```

### All options below

```shell
$ poetry run python ec2-tmux-cssh.py --help
Usage: ec2-tmux-cssh.py [OPTIONS]

Options:
  --is-ecs                   Find ec2 instances where ecs service runs on
  --ecs-cluster TEXT         ECS Cluster where ECS Service runs on
  --ecs-service TEXT         ECS Service we want to find EC2 instances for
  --hosts-tag-key TEXT       Tag key to find hosts with
  --hosts-tag-value TEXT     Tag value to find hosts with
  --hosts-ssh-key TEXT       SSH Private Key for hosts
  --hosts-user TEXT          SSH user for hosts
  --use-bastion              Proxy SSH through a bastion host
  --bastions-tag-key TEXT    Tag key to find bastions with
  --bastions-tag-value TEXT  Tag value to find bastions with
  --bastion-name TEXT        Bastion EC2 Name
  --bastion-ssh-key TEXT     SSH Private Key for bastion
  --bastion-user TEXT        SSH user for bastion
  --help                     Show this message and exit.
```
