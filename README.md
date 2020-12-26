# ec2-tmux-cssh

## Overview

tmux cluster ssh to multiple ec2 instances via bastion host

## Requirements

- AWS access to [DescribeInstances](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html)
- Private ssh keys for the servers you will try to connect to in `~/.ssh`
- [tmux-cssh](https://github.com/zinic/tmux-cssh/blob/042fdec2dc51bcfe62499e72f589dc9c146ab71a/tmux-cssh) in your `${PATH}`
- [poetry](https://github.com/python-poetry/poetry)

## Before first run

1. `poetry install`

## How to use

```
$ cd /path/to/this/repository
$ AWS_PROFILE=your-aws-profile poetry run python ec2-tmux-cssh
[?] What tag_key should I use to find bastions?: Role
   Name
 > Role
   aws:autoscaling:groupName
   aws:cloudformation:logical-id
   aws:cloudformation:stack-id
   aws:cloudformation:stack-name
   aws:ec2launchtemplate:id
   aws:ec2launchtemplate:version

[?] What tag_key should I use to find instances?: Name
 > Name
   Role
   aws:autoscaling:groupName
   aws:cloudformation:logical-id
   aws:cloudformation:stack-id
   aws:cloudformation:stack-name
   aws:ec2launchtemplate:id
   aws:ec2launchtemplate:version

[?] What Role value should I use to find bastions?: bastion
   DB
 > bastion

[?] What Name value should I use to find instances?: qa-ecs-cluster
 > qa-ecs-cluster
   rabbitmq
   ecs-cluster

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

I will tmux-cssh through bastion qa-bastion to these IPs: ['10.10.21.104', '10.10.21.230', '10.10.21.223', '10.10.20.118', '10.10.20.83', '10.10.20.39']
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.21.104'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.21.230'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.21.223'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.20.118'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.20.83'
* Connecting 'ssh  -o ProxyCommand='ssh -i /Users/macuser/.ssh/qa-bastion.pem ubuntu@SomePublicIP -W %h:%p' -i /Users/macuser/.ssh/qa.pem ec2-user@10.10.20.39'
[exited]
```
