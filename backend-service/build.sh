#!/usr/bin/env bash

# Checkout our projectcd
cd /tmp
git clone https://github.com/nicc777/k8s-kafka-experiment.git
cd k8s-kafka-experiment/backend-service

ehoc "- Current directory: ${PWD}"

# Set version with:
#   export APP_VERSION=vN 
# Where N is "v1", "v2" or "v3"
: ${APP_VERSION:="v1"}

echo "- Building application version ${APP_VERSION}"

echo "- Packaging Configmap's for Python files"

echo "  - raw_data_generator"
kubectl create configmap raw_data_generator-main-cm --from-file=v1/raw_data_generator/main.py -n exp
kubectl describe configmap raw_data_generator-main-cm -n exp


