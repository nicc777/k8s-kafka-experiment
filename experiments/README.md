
- [Experiments Root](#experiments-root)
- [Initial Preparations (once off)](#initial-preparations-once-off)
  - [Ingress](#ingress)
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

## Ingress

If services are exposed as `NodePort`, we can use `socat` to forward the traffic directly to the services, instead of using `kubectl port-forward`. 

Add the following host names to your `/ect/hosts` file under the `127.0.0.1` host:

* argocd.example.tld
* kafka-ui.example.tld
* tekton-ui.example.tld
* tekton-iac.example.tld
* tekton-app.example.tld
* demo.example.tld
* traefik-dashboard.example.tld

## ArgoCD

For this purpose, it is important to create a number of port-forwarding connections:

```shell
# Enable the Ingress for ArgoCD
kubectl apply -f cicd_base/argocd-nodeport.yaml
```

In order to get the ArgoCD admin password, run:

```shell
# Run in Terminal 2 to get the ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

The ArgoCD Web UI is now available on https://argocd.example.tld/

> [!NOTE]
> You may have to accept the certificate exception in your web browser


## Tekton

Next, setup Tekton:

```shell
# Install Tekton base
kubectl apply -f cicd_base/applications/01_tekton.yaml

# Install pipelines required for setting up the experiments
kubectl apply -f cicd_base/applications/02_tekton_pipelines.yaml

# Setup Ingress
kubectl apply -f cicd_base/tekton-nodeport.yaml
```

Tekton UI: The Tekton dashboard is available at http://tekton-ui.example.tld/#/taskruns (`TaskRun` instances is what we are most interested in)

# Running a experiment

There are several steps to start each experiment

## Step 1: Preparing Kafka and Kafka UI

Ensure the values for the Kafka UI still matches your desired configuration

```shell
# In terminal 4, run the following command to install the base requirements: Valkey and Kafka
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"apply"}' http://tekton-iac.example.tld

# You can verify the installation worked by looking at the TaskRun results:
kubectl get TaskRuns -n default                                                       

# Note the latest task run name, for example "helm-pipelines-run-ppqrb" - replace this in TASKRUN-NAME below: 
# Now get the logs:
kubectl logs TASKRUN-NAME-pod -c step-manage-base-resources -n default
```

Open the Kafka UI in the browser: http://kafka-ui.example.tld/

## Step 2: Running the experiment

The experiments can be controlled by the command-and-control pipeline, for which another terminal is required for port forwarding:

```shell
# TEST:
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"test", "app_version": "v1"}' http://tekton-app.example.tld
```

Other `command` options include:

| Command                        | Use Case                                                                                 |
| ------------------------------ | ---------------------------------------------------------------------------------------- |
| `test`                         | Required for testing. The values for `app_version` and `canary_config` is not important. |
| `build_and_deploy_app_version` | Deploys a specific version, as dictated by the experiment to be run.                     |
| `delete_app_version`           | Deletes a specific application version, as dictated by the experiment                    |
| `deploy_canary`                | Used to set the load balancing options between two versions of an application.           |
| `delete_canary`                | Reset all routing to the selected application version                                    |

Change into the relevant experiment sub-directory and follow the instructions in the README.

List of experiment:

| Experiment                   | Experimental Objectives                                                  |
| ---------------------------- | ------------------------------------------------------------------------ |
| [exp-01](./exp-01/README.md) | Basic deployment of workload V1                                          |
| [exp-02](./exp-02/README.md) | Basic deployment of workload V2                                          |
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
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete"}' http://tekton-iac.example.tld
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
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"deploy_debug_app", "app_version": "v2"}' http://tekton-app.example.tld

# Delete the deployment:
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_debug_app", "app_version": "v2"}' http://tekton-app.example.tld

# Deploy with the script "backend-service/debug_code_apps/schema_version_selection_poc.py"
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"deploy_debug_app", "app_version": "backend-service/debug_code_apps/schema_version_selection_poc.py"}' http://tekton-app.example.tld

# Delete the deployment:
curl -vvv -X POST -H 'Content-Type: application/json' -d '{"command":"delete_debug_app", "app_version": "backend-service/debug_code_apps/schema_version_selection_poc.py"}' http://tekton-app.example.tld
```

