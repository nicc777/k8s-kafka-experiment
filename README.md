
- [k8s-kafka-experiment](#k8s-kafka-experiment)
  - [Project Progress](#project-progress)
- [Workload Description used to Exercise Kafka](#workload-description-used-to-exercise-kafka)
- [Kubernetes Platform for the Lab](#kubernetes-platform-for-the-lab)
- [References and resources](#references-and-resources)


# k8s-kafka-experiment

Just some experiments on running Kafka and simple applications in Kubernetes, exploring various operational scenarios around schema management and application upgrades requiring schema changes in order to explore various upgrade strategies, for example blue/green, canary etc.

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

To start experimenting, start with the [Experiment README](./experiments/README.md)

## Project Progress

<!-- 
Icons:

DONE              :white_check_mark:
Work in Progress  :construction:
Not Started       :hourglass:
-->

| Major Feature               | Description                                               | Status             | Status Notes                                                                                 |
|-----------------------------|-----------------------------------------------------------|--------------------|----------------------------------------------------------------------------------------------|
| Infrastructure Preparations | Manifests and documentation to setup the experimental Lab | :white_check_mark: | Considering this done. Might be some improvements to come over time.                         |
| Application v1              | Application with basic data flow via Kafka                | :white_check_mark: | Done                                                                                         |
| Application Upgrade Process | Add pipelines to automate blue/green & canary deployments | :white_check_mark: | Done                                                                                         |
| Application v2              | Add feature to count widget defects                       | :white_check_mark: | Done                                                                                         |
| Application v3              | Add total manufacturing cost data                         | :construction:     | Not started                                                                                  |
| Reliability Experiment      | Chaos testing                                             | :hourglass:        | Not started                                                                                  |

The idea is to use blue/gree with canary deployments between application upgrades.

# Workload Description used to Exercise Kafka

Refer to the document [WORKLOADS.md](./WORKLOADS.md) for a more detailed description of the applications being deployed in this experiment.

# Kubernetes Platform for the Lab

Refer to the document [LAB.md](./LAB.md) for setting up a lab environment.

# References and resources

* [Confluent example using basic platform deployment with a Schema registry](https://github.com/confluentinc/confluent-kubernetes-examples/tree/master/schemas) (based on commit `master` branch with the last commit being [cdd460dd](https://github.com/confluentinc/confluent-kubernetes-examples/tree/cdd460dd90fbf3abfb348ed43acf97e3167399bd))
  * [Quick Start for Confluent Platform](https://docs.confluent.io/platform/7.7/get-started/platform-quickstart.html#quickstart)
  * [Deploy and Manage Confluent Platform Using Confluent for Kubernetes](https://docs.confluent.io/operator/current/overview.html)
  * [Schema Registry Concepts for Confluent Platform](https://docs.confluent.io/platform/current/schema-registry/fundamentals/index.html)
  * [Tutorial: Use Schema Registry on Confluent Platform to Implement Schemas for a Client Application](https://docs.confluent.io/platform/7.7/schema-registry/schema_registry_onprem_tutorial.html)
  * [Confluent Operator for Kubernetes API Reference](https://docs.confluent.io/operator/current/co-api.html)
* Tested on the [microk8s](https://microk8s.io/) Kubernetes distro, running on a single host. AT the time of creating this experiment, Kubernetes was at version 1.30
  * [Addons Documentation](https://microk8s.io/docs/addons)
* The [Kafka UI](https://github.com/provectus/kafka-ui) project and [documentation](https://docs.kafka-ui.provectus.io/)
  * [Kafka UI Helm Charts](https://docs.kafka-ui.provectus.io/configuration/helm-charts/quick-start) documentation
* Valkey Resources:
  * [Valkey Home Page](https://valkey.io/)
  * Bitnami Managed [Helm Chart](https://github.com/bitnami/charts/blob/main/bitnami/valkey/README.md)
* This project use a [generic Python container](https://github.com/nicc777/container-python4aws) with all the require libraries, packages and other tools pre-installed for easy Python script deployment and testing in Kubernetes
* Tekton related resources:
  * [Home Page](https://tekton.dev/)
  * [Trigger Examples](https://github.com/tektoncd/triggers/tree/main/examples)
* Python COnfluent References:
  * [Python Client for Apache Kafka](https://docs.confluent.io/kafka-clients/python/current/overview.html)
  * [Library API Documentation](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#)

> [!NOTE]
> The following references are included as I tried using the newer Gateway API implementation as a replacement for Ingress, but for services like ArgoCD that required `TLSRoute` configurations, I had to enable experimental features. I spent a lot of time on Nginx but failed to get it working properly. Mostly, if I got one thing to work, something else would break - basically I could have either a working `HTTPRoute` or a working `TLSRoute` - but never both. I also tried Traefik but quickly run into very similar issues and that decided to abandon this effort (at least for now). Instead I will rely on a more traditional Ingress approach, using Traefik, since I just know the product a little better. I prefer using a `TraefikService` kind for load balancing between services over a very different approach in Nginx Ingress (see [this Nginx example](https://www.elvinefendi.com/2018/11/25/canary-deployment-with-ingress-nginx.html)).

* Kubernetes Gateway API Resources:
  * [SIG Documentation](https://gateway-api.sigs.k8s.io/)
  * [Kubernetes Documentation](https://kubernetes.io/docs/concepts/services-networking/gateway/)
  * [Implementations](https://gateway-api.sigs.k8s.io/implementations/)
  * Nginx Gateway Fabric:
    * [Overview](https://docs.nginx.com/nginx-gateway-fabric/overview/)
    * [Installing With Helm (NodePort Target)](https://docs.nginx.com/nginx-gateway-fabric/installation/installing-ngf/helm/)
    * [Basic Traffic Routing to Applications](https://docs.nginx.com/nginx-gateway-fabric/how-to/traffic-management/routing-traffic-to-your-app/)
    * [More complex routing, including weighted routing (canary)](https://blog.nginx.org/blog/how-nginx-gateway-fabric-implements-complex-routing-rules)

