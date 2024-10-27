
- [k8s-kafka-experiment](#k8s-kafka-experiment)
  - [Project Progress](#project-progress)
- [Workload Description used to Exercise Kafka](#workload-description-used-to-exercise-kafka)
  - [Basic Workload Scenario](#basic-workload-scenario)
  - [Workflow Versions](#workflow-versions)
    - [Version 1: Basic Data](#version-1-basic-data)
    - [Version 2: Adding Widget Defects](#version-2-adding-widget-defects)
    - [Version 3: Adding Total Manufacturing Cost](#version-3-adding-total-manufacturing-cost)
- [Kubernetes Platform](#kubernetes-platform)
- [References and resources](#references-and-resources)


# k8s-kafka-experiment

Just some experiments on running Kafka and simple applications in Kubernetes, exploring various operational scenarios around schema management and application upgrades requiring schema changes in order to explore various upgrade strategies, for example blue/green, canary etc.

> [!WARNING]
> The content provided here are for experimentation and learning. It is not intended for production systems and in many cases may ignore security configurations required for production systems.
>
> USE AT YOUR OWN RISK

To start experimenting, start with the [Experiment README](./experiments/README.md)

## Project Progress

| Major Feature               | Description                                               | Status         | Status Notes                                                                                 |
|-----------------------------|-----------------------------------------------------------|----------------|----------------------------------------------------------------------------------------------|
| Infrastructure Preparations | Manifests and documentation to setup the experimental Lab | :construction: | Mostly done, but still more need to migrate to Tekton pipelines. Still too many manual steps |
| Application v1              | Application with basic data flow via Kafka                | :construction: | Started working on some code, but still a far way to go.                                     |
| Application Upgrade Process | Add pipelines to automate blue/green & canary deployments | :hourglass:    | Not started                                                                                  |
| Application v2              | Add feature to count widget defects                       | :hourglass:    | Not started                                                                                  |
| Application v3              | Add total manufacturing cost data                         | :hourglass:    | Not started                                                                                  |
| Reliability Experiment      | Chaos testing                                             | :hourglass:    | Not started                                                                                  |

The idea is to use blue/gree with canary deployments between application upgrades.

# Workload Description used to Exercise Kafka

Click the below image for a full-size version:

<a href="https://raw.githubusercontent.com/nicc777/k8s-kafka-experiment/refs/heads/main/diagrams/experimental-design.png" target="_blank">   <img src="https://raw.githubusercontent.com/nicc777/k8s-kafka-experiment/refs/heads/main/diagrams/experimental-design-thumbnail.png" alt="Design Diagram" width="256" height="321">  </a>

For the experiments the same application is used in all experiments. The application has essentially three versions in order to also experiment with various application upgrades, where each upgrade adds more data to the data schema.

## Basic Workload Scenario

The workload comprises of several individual deployments:

| Deployment         | Function                                                                                                                                                                                               | Kafka Producers Topics | Kafka Consumers Topics |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|------------------------|
| Raw Data Generator | Generates random raw data                                                                                                                                                                              | raw-data-in            | n/a                    |
| Back End           | Consumes raw data, processes it and stores results in a local DB (memory cache). Periodically the summary stats is published to a summary topic                                                        | summary-stats          | raw-data-in            |
| Summary Stats UI   | Consumes the summary statistics and updates a local summary state DB (memory cache). A Web front-end component (REST based) can be called to retrieve the last updated summary statistics from the DB. | n/a                    | summary-stats          |

## Workflow Versions

The basic raw data is counting the number of widgets created per hour and as we have more data to work with, we adapt the schema used to push the data through the Kafka platform and consume it by the various deployed components.

The scenario demonstrates how a very simple data processing pipeline could be used. The scenario will generate a random data set with the following starting parameters (version 1):

* Spanning years: from January 2000 to February 2024
* If a random timestamp is outside working hours,  the QTY's will all be `0`
  * Working hours: 08.00 to 20.00 (12 hours), 7 days a week, including all public holidays - no mercy !!
* The QTY of manufactured widgets in working hours will fall in a range from 50 to 100, randomly selected for each hour

### Version 1: Basic Data

Example of the raw data in JSON format:

```json
{
    "sku": "string",
    "manufactured_qty": 0,
    "year": 2024,
    "month": 1,
    "day": 15,
    "hour": 3
}
```

On the backend, the data will be aggregated using the `sku` and `timestamp` data as the index with the manufactured QTY as the numeric value.

The summary data REST data structure is expected to look like this:

```json
{
    "description": "Summary aggregated statistics per SKU per year and month",
    "data": [
        {
            "year": 2024,
            "month": 1,
            "manufacturing": [
                {
                    "sku": "string",        
                    "totals": {
                        "manufactured_qty": 1020
                     }
                }
            ]
        }
    ]
}
```

### Version 2: Adding Widget Defects

In version 2, we add a number of defective widgets, which will result in a smaller volume available for selling

The QTY of defects will be a random percentage of the total widgets for that hour, with a minimum of 1 widget and a maximum of the total qty of widgets minus 25:

```python
import random

DEFECTS_MIN = 1
DEFECTS_MAX_SUBTRACTOR = 25
MIN_WIDGETS = 50
MAX_WIDTGETS = 100

def max_defects_possible(base_qty: int)->int:
    return base_qty - DEFECTS_MAX_SUBTRACTOR

def calc_final_defect_qty(base_qty:int)->int:
    defects_max = max_defects_possible(base_qty=base_qty)
    defect_percentage = random.randrange(1,100)/100
    defect_qty = int(qty_widgets_manufactured * defect_percentage)
    if defect_qty > defects_max:
        defect_qty = defects_max
    if defect_qty < 1:
        defect_qty = 1
    return defect_qty

qty_widgets_manufactured = random.randrange(MIN_WIDGETS,MAX_WIDTGETS)
qty_defects = calc_final_defect_qty(base_qty=qty_widgets_manufactured)
```

Example of the raw data in JSON format:

```json
{
    "sku": "string",
    "manufactured_qty": 0,
    "defect_qty": 0,
    "year": 2024,
    "month": 1,
    "day": 15,
    "hour": 3
}
```

The summary data REST data structure is expected to look like this:

```json
{
    "description": "Summary aggregated statistics per SKU per year and month",
    "data": [
        {
            "year": 2024,
            "month": 1,
            "manufacturing": [
                {
                    "sku": "string",        
                    "totals": {
                        "manufactured_qty": 1020,
                        "defect_qty": 55
                     }
                }
            ]
        }
    ]
}
```

### Version 3: Adding Total Manufacturing Cost

In version 3, we add the manufacturing costs fo the widgets.

The cost is based on the year and is calculated as a base cost, plus a cost per widget

* Starting base cost: 280 units per hour
  * Annual increase: An integer value ranging in a random percentage between 5% and 10% (minimum 1)
  * The base cost can be aggregated for the month, based on the total work hours in that month
* Widget cost (per SKU): Random integer value between 100 and 200
  * Annual increase a random integer value of minimum 1 or maximum 10% of of widget cost

Example of the raw data in JSON format:

```json
{
    "sku": "string",
    "manufactured_qty": 0,
    "defect_qty": 0,
    "sku_manufacturing_cost": 120,
    "year": 2024,
    "month": 1,
    "day": 15,
    "hour": 3
}
```

The summary data REST data structure is expected to look like this:

```json
{
    "description": "Summary aggregated statistics per SKU per year and month",
    "data": [
        {
            "year": 2024,
            "month": 1,
            "base_cost": 123456,
            "total_manufacturing_cost": 123456,
            "manufacturing": [
                {
                    "sku": "string",        
                    "totals": {
                        "manufactured_qty": 1020,
                        "defect_qty": 55,
                        "production_cost": 123456
                    }
                }
            ]
        }
    ]
}
```

Note: The `total_manufacturing_cost` must be the sum total of every SKU's `production_cost`


# Kubernetes Platform

The experiment is based on a `microk8s` version 1.30 with the following key addons enabled:

* Required:
  * argocd
  * dns
  * hostpath-storage
* Optional, but may be useful
  * dashboard
  * ingress
  * metrics-server
  * registry

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
  * [Addons Documentation](https://microk8s.io/docs/addons)
* The [Kafka UI](https://github.com/provectus/kafka-ui) project and [documentation](https://docs.kafka-ui.provectus.io/)
  * [Kafka UI Helm Charts](https://docs.kafka-ui.provectus.io/configuration/helm-charts/quick-start) documentation
* Valkey Resources:
  * [Valkey Home Page](https://valkey.io/)
  * Bitname Managed [Helm Chart](https://github.com/bitnami/charts/blob/main/bitnami/valkey/README.md)
* This project use a [generic Python container](https://github.com/nicc777/container-python4aws) with all the require libraries, packages and other tools pre-installed for easy Python script deployment and testing in Kubernetes
