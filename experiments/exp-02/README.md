
- [Experiment 2 - Basic Functional Test, with version 2 of the Application](#experiment-2---basic-functional-test-with-version-2-of-the-application)
- [Deploy Application Stack v2](#deploy-application-stack-v2)
- [Update the Load Balancing](#update-the-load-balancing)
  - [Basic Testing](#basic-testing)
- [Cleanup](#cleanup)


# Experiment 2 - Basic Functional Test, with version 2 of the Application

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

This experiment is essentially exactly the same as [experiment 1](../exp-01/README.md), but with version to of the application.

# Deploy Application Stack v2

Run the following:

```shell
# Deploy V1
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"build_and_deploy_app_version", "app_version": "v1"}' http://tekton-app.example.tld

# Deploy V2
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"build_and_deploy_app_version", "app_version": "v2"}' http://tekton-app.example.tld
```

# Update the Load Balancing

It's best to wait a minute or two until the deployments of the previous step is complete and all Pods are running normally.

Split the traffic 50/50 between the two running versions:

```shell
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"deploy_canary", "canary_config": "v1:50,v2:50", "domain": "example.tld"}' http://tekton-app.example.tld
```

## Basic Testing

Before testing, it's best to wait a couple of minutes for the initial data to be generated. Two to three minutes should be more than enough.

> [!NOTE]  
> Data is generated randomly, and therefore your actual results may be different from that shown below.

To use the supplied Python CLI client, ensure the following is installed:

```shell
pip3 install tabulate requests
```

Now, use the supplied client:

```shell
python3 python3 client/app.py
```

In the client you should see various updates comming in from different API versions. Version 2 API's will include data related to the number of defects, where version 1 API's do not.

# Cleanup

Run the following to remove the application:

```shell
# Remove the ingress
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_canary"}' http://tekton-app.example.tld

# Remove the deployed versions
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_app_version", "app_version": "v1"}' http://tekton-app.example.tld

curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_app_version", "app_version": "v2"}' http://tekton-app.example.tld
```
