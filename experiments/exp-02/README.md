
- [Experiment 2 - Basic Functional Test, with version 2 of the Application](#experiment-2---basic-functional-test-with-version-2-of-the-application)
- [Deploy Application Stack v1](#deploy-application-stack-v1)
- [Connecting to the API End-Point](#connecting-to-the-api-end-point)
  - [Basic Testing](#basic-testing)
- [Cleanup](#cleanup)


# Experiment 2 - Basic Functional Test, with version 2 of the Application

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

This experiment is essentially exactly the same as [experiment 1](../exp-01/README.md), but with version to of the application.

# Deploy Application Stack v1

Run the following:

```shell
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"build_and_deploy_app_version", "app_version": "v2"}' http://tekton-app.example.tld
```

# Connecting to the API End-Point

Once the application is deployed, you should see a number of Pods with `kubectl get pods -n exp`:

The `front-end-ui-rest-*` pods are the ones we need to connect to, therefore you need to ensure at least one Pod is fully `ready`.

Now you get setup port forwarding to the Rest API:

```shell
kubectl port-forward --address=0.0.0.0 -n exp service/rest-api-v2 7098:8080
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

# Cleanup

Run the following to remove the application:

```shell
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_app_version", "app-version": "v2"}' http://tekton-app.example.tld
```
