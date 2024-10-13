# k8s-kafka-experiment

Just some experiments on running Kafka and simple applications in Kubernetes, exploring various operational scenarios around schema management and application upgrades requiring schema changes in order to explore various upgrade strategies, for example blue/green, canary etc.

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

To start experimenting, start with the [Experiment README](./experiments/README.md)

# Workload Description used to Exercise Kafka

Click the below image for a full-size version:

<a href="">   <img src="img_girl.jpg" alt="Design Diagram" width="256" height="365">  </a>

For the experiments the same application is used in all experiments. The application has essentially three versions in order to also experiment with various application upgrades, where each upgrade adds more data to the data schema.

# Kubernetes Platform

The experiment is based on a `microk8s` version 1.30 with the following key plugins enabled:

* xxx

To get the ArgoCD admin password, run:

```shell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

To start a port forwarder to ArgoCD UI:

```shell
kubectl port-forward service/argo-cd-argocd-server -n argocd --address=0.0.0.0 7070:443
```

# References and resources

* [Confluent example using basic platform deployment with a Schema registry](https://github.com/confluentinc/confluent-kubernetes-examples/tree/master/schemas) (based on commit `master` branch with the last commit being [cdd460dd](https://github.com/confluentinc/confluent-kubernetes-examples/tree/cdd460dd90fbf3abfb348ed43acf97e3167399bd))
  * [Quick Start for Confluent Platform](https://docs.confluent.io/platform/7.7/get-started/platform-quickstart.html#quickstart)
  * [Deploy and Manage Confluent Platform Using Confluent for Kubernetes](https://docs.confluent.io/operator/current/overview.html)
  * [Schema Registry Concepts for Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/index.html)
  * [Tutorial: Use Schema Registry on Confluent Platform to Implement Schemas for a Client Application](https://docs.confluent.io/platform/7.7/schema-registry/schema_registry_onprem_tutorial.html)
* Tested on the [microk8s](https://microk8s.io/) Kubernetes distro, running on a single host. AT the time of creating this experiment, Kubernetes was at version 1.30
* The [Kafka UI](https://github.com/provectus/kafka-ui) project and [documentation](https://docs.kafka-ui.provectus.io/)
  * [Kafka UI Helm Charts](https://docs.kafka-ui.provectus.io/configuration/helm-charts/quick-start) documentation
