# Experiment 1 - Basic Functional Test

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

Ensure you have followed the initial preparations as described [here](../README.md)

# Deploy Application Stack v1

Run the following:

```shell
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"build_and_deploy_app_version", "app-version": "v1", "canary_config": "v1:90,v2:10"}' http://127.0.0.1:7092
```

# Cleanup

Run the following to remove the applictaion:

```shell
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_app_version", "app-version": "v1", "canary_config": "v1:90,v2:10"}' http://127.0.0.1:7092
```

