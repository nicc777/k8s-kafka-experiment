# Experiments Root

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

Each directory is an experiment on it's own.

All applications will be installed in the namespace `exp`.

# Initial Preparations (once off)

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
# Assuming you are in this project's root directory, Change into the "experiments" directory:
cd experiments 

# Deploy the Kafka operator
helm upgrade --install -n confluent confluent-operator confluentinc/confluent-for-kubernetes

# Deploy the main kafka components - the actual schema configurations will be applied in each experiment as needed
kubectl apply -f confluent-platform.yaml

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

| Experiment | Experimental Objectives |
|------------|-------------------------|
| TODO       | TODO                    |

## Step 3: Post Experiment Cleanup

Before each experiment starts, ensure the previous experiment was completely removed:

```shell
# Follow these steps after you followed the specific experiment cleanup instructions

# IMPORTANT: Ensure you are back into the ./experiments directory from the project root directory perspective. If you were in a specific experiment directory, go back one level:
cd ../

# Delete the Kafka UI
helm delete -n confluent kafka-ui

# Delete the running Kafka components
kubectl delete -f confluent-platform.yaml
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


