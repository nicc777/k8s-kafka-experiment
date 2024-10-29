#!/usr/bin/env bash

# Checkout our projectcd
cd /tmp/k8s-kafka-experiment/backend-service

echo "- Current directory: ${PWD}"

# Set version with:
#   export APP_VERSION=vN 
# Where N is "v1", "v2" or "v3"
: ${APP_VERSION:="v1"}

echo "- Building application version ${APP_VERSION}"

echo "- Packaging Configmap's for Python files"

# FIXME - I need another approach, as I cannot commit and push these changes....
echo "  - raw_data_generator"
kubectl create configmap raw-data-generator-cm --from-file=$APP_VERSION/raw_data_generator/main.py --dry-run=client -o yaml > /tmp/k8s-kafka-experiment/experiments/argocd/deployments/cell-app/$APP_VERSION/deployment.yaml
kubectl describe configmap raw_data_generator-main-cm -n exp


