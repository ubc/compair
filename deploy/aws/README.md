Deploying ComPAIR on Amazon Web Services
=======================================

This instruction uses CloudFormation template to deploy ComPAIR application to AWS. By default, it will deploy a MySQL RDS as the backend database, 1 instance of EC2 and 4 docker containers for the application, worker, redis, and a load balancer to accept the request.

The parameters in the template can be changed based on deployment requirement.

Prerequisites
-------------
* AWS account with billing enabled
* [AWS commandline tool](https://aws.amazon.com/cli/)
* The files in this directory


Deploying ComPAIR
-----------------

### Deploying the Stack
Replace YOUR_KEY with appropriate value in your AWS environment, e.g. your [ssh key name](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html). You may also want to replace the default database password in the template.
```bash
export KEYNAME=YOUR_KEY # Name of an existing EC2 KeyPair to enable SSH access to the ECS instances.
aws cloudformation create-stack --stack-name compair --template-body file:///`pwd`/compair.template.json --parameters ParameterKey=KeyName,ParameterValue=$KEYNAME --capabilities CAPABILITY_IAM
```
The provision progress can be monitored through AWS CloudFormation console or running the command below. The application URL can be found in `output` tab in the console.

```
aws cloudformation describe-stack-events --stack-name compair
```

### Initializing App

Once the stack is started, login to the ec2 instance to run the initializing command. To find the instance external domain:
```
aws ec2 describe-instances
```
Find the domain like `ec2-xxx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com` and ssh with ec2-user
```
ssh ec2-user@ec2-xxx-xxx-xxx-xxx.us-west-2.compute.amazonaws.com
```
You should be logged in with ssh key without password.

Find the app container ID. If nothing showed up, wait for a few minutes.
```
docker ps | grep "\-compair-app"
```

Execute the database command:
```
docker exec CONTAINER_ID ./manage.py database create
```

Once finished, ComPAIR should be accessible with default user `root`/`password`.

Tearing Down
--------------------

```bash
aws cloudformation delete-stack --stack-name compair
```
