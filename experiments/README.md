
- [Experiments Root](#experiments-root)
- [Initial Preparations (once off)](#initial-preparations-once-off)
  - [Nginx Gateway API Fabric](#nginx-gateway-api-fabric)
  - [ArgoCD](#argocd)
  - [Tekton](#tekton)
- [Running a experiment](#running-a-experiment)
  - [Step 1: Preparing Kafka and Kafka UI](#step-1-preparing-kafka-and-kafka-ui)
  - [Step 2: Running the experiment](#step-2-running-the-experiment)
  - [Step 3: Post Experiment Cleanup](#step-3-post-experiment-cleanup)
- [Final Cleanup](#final-cleanup)
- [Running a Debug Container](#running-a-debug-container)


# Experiments Root

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

Each directory is an experiment on it's own.

All applications will be installed in the namespace `exp`.

# Initial Preparations (once off)

In order to run the experiment, access to several component API's or web user interfaces may be required.

For running the experiments, you may need as many as 6 open terminal sessions.

## Nginx Gateway API Fabric

In order to expose the application, and to test blue/green with canary deployment strategies, we need a Gateway API solution.

NGinx provides a fairly straight forward solution to expose the Gateway using Node Ports:

```shell
# The experimental features are required for TLSRoute (as on 2024-11-09)
kubectl kustomize "https://github.com/nginxinc/nginx-gateway-fabric/config/crd/gateway-api/experimental?ref=v1.4.0" | kubectl apply -f -

# Wait until the previous components are all deployed...
helm install ngf oci://ghcr.io/nginxinc/charts/nginx-gateway-fabric --create-namespace -n nginx-gateway --set nginxGateway.gwAPIExperimentalFeatures.enable=true --set service.type=NodePort
```

> [!NOTE]
> When you see the following error in the Nginx logs On Ubuntu Server, ensure IPv6 is enabled: "_socket() :80 failed (97: Address family not supported by protocol)_" 

Next, get the HTTP and HTTPS NodePort values for the gateway:

```shell
kubectl get services -n nginx-gateway
```

Expect the outpit to look something like this:

```text
NAME                       TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
ngf-nginx-gateway-fabric   NodePort   10.152.183.68   <none>        80:30657/TCP,443:31090/TCP   21m
```

For convenience, you can use `socat` to forward traffic to your cluster NodePort services of the Gateway API:

```shell
# In Terminal 1, Forward TSL traffic. Use the NodPort value from the previous command (for example 31090)
export CLUSTER_ADDRESS=...
export GW_TLS_PORT=...
sudo socat TCP-LISTEN:443,fork,reuseaddr TCP:$CLUSTER_ADDRESS:$GW_TLS_PORT

# In terminal 2, forward HTTP traffic:
export CLUSTER_ADDRESS=...
export GW_HTTP_PORT=...
sudo socat TCP-LISTEN:80,fork,reuseaddr TCP:$CLUSTER_ADDRESS:$GW_HTTP_PORT
```

And add these domains to your hosts file for `127.0.0.1`:

* argocd.example.tld - For using ArgoCD in a Web Browser
* kafka-ui.example.tld - For using the Kafka web UI
* tekton-ui.example.tld - For using the Tekton Web UI
* tekton-iac.example-tld - Will route calls to the Tekton pipeline for provisioning Infrastructure
* tekton-app.example.tld - Will route calls to the Tekton pipeline for application management


## ArgoCD

For this purpose, it is important to create a number of port-forwarding connections:

```shell
# ArgoCD in Terminal 1 (alternative of using the Gateway API, as describe in the section "Nginx Gateway API Fabric")
kubectl port-forward service/argo-cd-argocd-server 7090:80 -n argocd
```

In order to get the ArgoCD admin password, run:

```shell
# Run in Terminal 2 to get the ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

The ArgoCD Web UI is now available on https://127.0.0.1:7090/ or https://argocd.example.tld/

> [!NOTE]
> You may have to accept the certificate exception in your web browser


## Tekton

Next, setup Tekton:

```shell
# Install Tekton base
kubectl apply -f cicd_base/applications/01_tekton.yaml

# Install pipelines required for setting up the experiments
kubectl apply -f cicd_base/applications/02_tekton_pipelines.yaml

# Finally, in Terminal 2, setup a port-forwarder to the Tekton Dashboard
kubectl port-forward service/tekton-dashboard 9097:9097 -n tekton-pipelines
```

The Tekton dashboard is available at http://127.0.0.1:9097/#/taskruns (`TaskRun` instances is what we are most interested in)

Finally, setup a port-forwarder to the Tekton pipelines webhook:

```shell
# The following runs in Terminal 3
kubectl port-forward service/el-helm-pipelines-event-listener 7091:8080 -n default
```

# Running a experiment

There are several steps to start each experiment

## Step 1: Preparing Kafka and Kafka UI

Ensure the values for the Kafka UI still matches your desired configuration

```shell
# In terminal 4, run the following command to install the base requirements: Valkey and Kafka
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"apply"}' http://127.0.0.1:7091

# You can verify the installation worked by looking at the TaskRun results:
kubectl get TaskRuns -n default                                                       

# Note the latest task run name, for example "helm-pipelines-run-ppqrb" - replace this in TASKRUN-NAME below: 
# Now get the logs:
kubectl logs TASKRUN-NAME-pod -c step-manage-base-resources -n default

# Start the Port Forwarder to the Kafka UI
# Use the "--address=0.0.0.0" parameter if you are running the experiment on another computer in order to expose the UI to your lab
kubectl port-forward --address=0.0.0.0 -n exp service/kafka-ui 8090:80
```

Open the Kafka UI in the browser: http://127.0.0.1:8090/

## Step 2: Running the experiment

The experiments can be controlled by the command-and-control pipeline, for which another terminal is required for port forwarding:

```shell
# Create port forwarding session:
kubectl port-forward service/el-app-ctrl-event-listener 7092:8080 -n default

# TEST:
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"test", "app-version": "v1", "canary_config": "v1:90,v2:10"}' http://127.0.0.1:7092
```

Other `command` options include:

| Command                        | Use Case                                                                                 |
|--------------------------------|------------------------------------------------------------------------------------------|
| `test`                         | Required for testing. The values for `app-version` and `canary_config` is not important. |
| `build_and_deploy_app_version` | Deploys a specific version, as dictated by the experiment to be run.                     |
| `delete_app_version`           | Deletes a specific application version, as dictated by the experiment                    |
| `deploy_canary`                | Used to set the load balancing options between two versions of an application.           |
| `delete_canary`                | Reset all routing to the selected application version                                    |

Change into the relevant experiment sub-directory and follow the instructions in the README.

List of experiment:

| Experiment                   | Experimental Objectives                                                  |
|------------------------------|--------------------------------------------------------------------------|
| [exp-01](./exp-01/README.md) | Basic deployment of workload V1                                          |
| exp-02                       | Basic deployment of workload V2                                          |
| exp-03                       | Basic deployment of workload V3                                          |
| exp-04                       | Deployment of V1 and upgrade to V2 using Blue Green with Canary strategy |

> [!NOTE]
> At this stage, future experiments will depend on the learnings from experiment 4.

## Step 3: Post Experiment Cleanup

Before each new experiment starts, ensure the previous experiment was completely removed:

```shell
# Kill the port forwarding in Terminals 4 before proceeding...

# Follow these steps after you followed the specific experiment cleanup instructions
# Cleanup the Memory caches and kafka operator
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete"}' http://127.0.0.1:7091
```

# Final Cleanup

Any additional deployments not covered in this guide.

Then, ensure all remaining port forwarding sessions are terminated.

Finally, remove Tekton:

```shell
# Remove pipelines required for setting up the experiments
kubectl delete -f cicd_base/applications/02_tekton_pipelines.yaml

# Remove Tekton base
kubectl delete -f cicd_base/applications/01_tekton.yaml
```

# Running a Debug Container

There is also an option to run a debug container, potentially with a custom script.

Python scripts are created in `backend-service/debug_code_apps/`, and can be managed with:

```shell
# Deploy the DEFAULT dummy.py
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"deploy_debug_app", "app_version": "v2"}' http://127.0.0.1:7092

# Delete the deployment:
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_debug_app", "app_version": "v2"}' http://127.0.0.1:7092

# Deploy with the script "backend-service/debug_code_apps/schema_version_selection_poc.py"
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"deploy_debug_app", "app_version": "backend-service/debug_code_apps/schema_version_selection_poc.py"}' http://127.0.0.1:7092

# Delete the deployment:
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_debug_app", "app_version": "backend-service/debug_code_apps/schema_version_selection_poc.py"}' http://127.0.0.1:7092
```

