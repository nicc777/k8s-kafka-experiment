


# Experiment 2 - Basic Functional Test, with version 2 of the Application

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

This experiment is essentially exactly the same as [experiment 1](../exp-01/README.md), but with version to of the application.

# Deploy Application Stack v1

Run the following:

```shell
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"build_and_deploy_app_version", "app_version": "v2"}' http://127.0.0.1:7092
```



