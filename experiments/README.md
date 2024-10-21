
- [Experiments Root](#experiments-root)
- [Initial Preparations (once off)](#initial-preparations-once-off)
  - [Install CI/CD Base](#install-cicd-base)
- [Running a experiment](#running-a-experiment)
  - [Step 1: Preparing Kafka and Kafka UI](#step-1-preparing-kafka-and-kafka-ui)
  - [Step 2: Running the experiment](#step-2-running-the-experiment)
  - [Step 3: Post Experiment Cleanup](#step-3-post-experiment-cleanup)
- [Final Cleanup](#final-cleanup)
- [Common Tasks](#common-tasks)
  - [ArgoCD](#argocd)
    - [Get the admin Password](#get-the-admin-password)
    - [Access the UI](#access-the-ui)


# Experiments Root

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

Each directory is an experiment on it's own.

All applications will be installed in the namespace `exp`.

# Initial Preparations (once off)

## Install CI/CD Base

Follow the instructions from [`cicd_base/README.md`](../cicd_base/README.md)


```shell
# Add the confluent Helm repo
helm repo add confluentinc https://packages.confluent.io/helm

# Add the confluent namespace
kubectl create namespace confluent

# Add the application experiment namespace
kubectl create namespace exp
```

# Running a experiment

There are several steps to start each experiment

## Step 1: Preparing Kafka and Kafka UI

Ensure the values for the Kafka UI still matches your desired configuration

```shell
# (OPTIONAL) Assuming you are in this project's root directory, Change into the "experiments" directory:
cd experiments 

# Deploy two Valkey (Memory Cache) instances to serve our back-end and UI as DB's
helm install -n exp -f ./valkey-backend-values.yaml valkey-backend oci://registry-1.docker.io/bitnamicharts/valkey

helm install -n exp -f ./valkey-ui-values.yaml valkey-ui oci://registry-1.docker.io/bitnamicharts/valkey

# Deploy the Kafka operator
helm upgrade --install -n confluent confluent-operator confluentinc/confluent-for-kubernetes

# Deploy the main kafka components - the actual schema configurations will be applied in each experiment as needed
kubectl apply -f ./kafka-platform-deployments/application/kafka-platform.yaml

# Deploy the Kafka UI (non-confluent project)
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm upgrade --install -n confluent -f kafka-ui-values.yaml kafka-ui kafka-ui/kafka-ui

# Start the Port Forwarder to the Kafka UI
# Use the "--address=0.0.0.0" parameter if you are running the experiment on another computer in order to expose the UI to your lab
kubectl port-forward --address=0.0.0.0 -n confluent service/kafka-ui 8090:80
```

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

Before each experiment starts, ensure the previous experiment was completely removed:

```shell
# Follow these steps after you followed the specific experiment cleanup instructions

# IMPORTANT: Ensure you are back into the ./experiments directory from the project root directory perspective. If you were in a specific experiment directory, go back one level:
cd ../

# Delete the Kafka UI
helm delete -n confluent kafka-ui

# Delete the running Kafka components
kubectl delete -f ./kafka-platform-deployments/application/kafka-platform.yaml

# Cleanup the Memory caches
helm delete -n exp valkey-backend valkey-ui
```

# Final Cleanup

Finally, remove the namespaces

```shell
# Delete the confluent kafka operator
helm delete confluent-operator -n confluent

# Cleanup namespaces
kubectl delete namespace confluent

kubectl delete namespace exp
```

# Common Tasks

## ArgoCD

### Get the admin Password

```shell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### Access the UI

```shell
kubectl port-forward service/argo-cd-argocd-server 7090:80 -n argocd
```

And open http://127.0.0.1:7090 in your browser.

> [!NOTE]
> By default the port forwarder will only listen on localhost. If you need to expose it on your LAN to access the UI from another computer, use the following instead:

```shell
kubectl port-forward service/argo-cd-argocd-server 7090:80 -n argocd --address 0.0.0.0
```


