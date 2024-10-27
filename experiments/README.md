
- [Experiments Root](#experiments-root)
- [Initial Preparations (once off)](#initial-preparations-once-off)
- [Running a experiment](#running-a-experiment)
  - [Step 1: Preparing Kafka and Kafka UI](#step-1-preparing-kafka-and-kafka-ui)
  - [Step 2: Running the experiment](#step-2-running-the-experiment)
  - [Step 3: Post Experiment Cleanup](#step-3-post-experiment-cleanup)
- [Final Cleanup](#final-cleanup)


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

For this purpose, it is important to create a number of port-forwarding connections:

```shell
# ArgoCD in Terminal 1
kubectl port-forward service/argo-cd-argocd-server 7090:80 -n argocd
```

In order to get the ArgoCD admin password, run:

```shell
# Run in Terminal 2 to get the ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

The ArgoCD Web UI is now available on https://127.0.0.1:7090/

> [!NOTE]
> You may have to accept the certificate exception in your web browser

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

# Now, in Terminal 4, run the following to 
cd experiments 

# Deploy the main kafka components - the actual schema configurations will be applied in each experiment as needed
kubectl apply -f ./kafka-platform-deployments/application/kafka-platform.yaml

# Deploy the Kafka UI (non-confluent project)
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm repo update
helm upgrade --install -n exp -f kafka-ui-values.yaml kafka-ui kafka-ui/kafka-ui

# Start the Port Forwarder to the Kafka UI
# Use the "--address=0.0.0.0" parameter if you are running the experiment on another computer in order to expose the UI to your lab
kubectl port-forward --address=0.0.0.0 -n exp service/kafka-ui 8090:80
```

Open the Kafka UI in the browser: http://127.0.0.1:8090/

## Step 2: Running the experiment

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

# IMPORTANT: Ensure you are back into the ./experiments directory from the project root directory perspective. If you were in a specific experiment directory, go back one level:
cd ../

# Delete the Kafka UI
helm delete kafka-ui -n exp

# Delete the running Kafka components
kubectl delete -f ./kafka-platform-deployments/application/kafka-platform.yaml

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



