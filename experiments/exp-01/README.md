
- [Experiment 1 - Basic Functional Test](#experiment-1---basic-functional-test)
- [Deploy Application Stack v1](#deploy-application-stack-v1)
- [Connecting to the API End-Point](#connecting-to-the-api-end-point)
  - [Basic Testing](#basic-testing)
- [Cleanup](#cleanup)

# Experiment 1 - Basic Functional Test

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

Ensure you have followed the initial preparations as described [here](../README.md)

# Deploy Application Stack v1

Run the following:

```shell
# The following shows the example of pushing the commend via Ingress
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"build_and_deploy_app_version", "app_version": "v1", "canary_config": "v1:90,v2:10"}' http://tekton-app.example.tld
```

# Connecting to the API End-Point

Once the application is deployed, you should see a number of Pods with `kubectl get pods -n exp`:

```text
NAME                                                READY   STATUS    RESTARTS   AGE
back-end-aggregator-producer-v1-67867fb966-sb5dm    1/1     Running   0          3m39s
back-end-demo-v1-57bd9586f8-fr4zs                   1/1     Running   0          3m39s
back-end-demo-v1-57bd9586f8-g4lpm                   1/1     Running   0          3m39s
back-end-demo-v1-57bd9586f8-prxj5                   1/1     Running   0          3m39s
front-end-aggregator-consumer-v1-7576f9dbc5-hv8xj   1/1     Running   0          3m39s
front-end-aggregator-consumer-v1-7576f9dbc5-srbqf   1/1     Running   0          3m39s
front-end-aggregator-consumer-v1-7576f9dbc5-tdsc2   1/1     Running   0          3m39s
front-end-ui-rest-v1-5564db45cf-4ckpc               1/1     Running   0          3m39s
front-end-ui-rest-v1-5564db45cf-dv6dl               1/1     Running   0          3m39s
front-end-ui-rest-v1-5564db45cf-f4sx6               1/1     Running   0          3m39s
front-end-ui-rest-v1-5564db45cf-kbl6j               1/1     Running   0          3m39s
front-end-ui-rest-v1-5564db45cf-pvzlg               1/1     Running   0          3m39s
kafka-ui-59f849bc88-g9vxs                           1/1     Running   0          5m57s
raw-data-generator-demo-v1-d54f7c9bd-22vx9          1/1     Running   0          3m39s
raw-data-generator-demo-v1-d54f7c9bd-8btsx          1/1     Running   0          3m39s
raw-data-generator-demo-v1-d54f7c9bd-p7fck          1/1     Running   0          3m39s
valkey-backend-primary-0                            2/2     Running   0          8m8s
valkey-backend-replicas-0                           2/2     Running   0          8m8s
valkey-frontend-primary-0                           2/2     Running   0          8m6s
valkey-frontend-replicas-0                          2/2     Running   0          8m6s
```

The `front-end-ui-rest-*` pods are the ones we need to connect to, therefore you need to ensure at least one Pod is fully `ready`.

Now you get setup port forwarding to the Rest API:

```shell
kubectl port-forward --address=0.0.0.0 -n exp service/rest-api-v1 7098:8080
```

## Basic Testing

Before testing, it's best to wait a couple of minutes for the initial data to be generated. Two to three minutes should be more than enough.

> [!NOTE]  
> Data is generated randomly, and therefore your actual results may be different from that shown below.

To test the Rest API, you can first try to get the SKU's with `curl http://127.0.0.1:7098/sku_names` which should get you the following result:

```json
{
    "names": [
        "SKU_799201",
        "SKU_019935",
        "SKU_641808"
    ]
}
```

To get specific data of a SKU, run `curl http://127.0.0.1:7098/query/SKU_799201/2020` to get the data:

```json
{
    "version": "v1",
    "data": [
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 1,
            "manufactured_qty": 426
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 2,
            "manufactured_qty": 495
        }
    ]
}
```

> [!NOTE]  
> Since not much time passed and provided you started from a clean slate, the data set may not yet include all the monthly data as there has no data been generated yet for all months. 

After waiting some more minutes, you may run the exact same request to see an update in the data:

```json
{
    "version": "v1",
    "data": [
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 1,
            "manufactured_qty": 38678
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 2,
            "manufactured_qty": 24493
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 3,
            "manufactured_qty": 18118
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 4,
            "manufactured_qty": 33624
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 5,
            "manufactured_qty": 24571
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 6,
            "manufactured_qty": 17544
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 7,
            "manufactured_qty": 16962
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 8,
            "manufactured_qty": 36474
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 9,
            "manufactured_qty": 41663
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 10,
            "manufactured_qty": 57263
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 11,
            "manufactured_qty": 43931
        },
        {
            "sku": "SKU_799201",
            "year": 2020,
            "month": 12,
            "manufactured_qty": 26230
        }
    ]
}
```

# Cleanup

Run the following to remove the application:

```shell
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_app_version", "app-version": "v1", "canary_config": "v1:90,v2:10"}' http://tekton-app.example.tld
```

