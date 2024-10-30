#!/usr/bin/env bash

# Checkout our projectcd
cd /tmp/k8s-kafka-experiment/backend-service

echo "- Current directory: ${PWD}"

# Set version with:
#   export APP_VERSION=vN 
# Where N is "v1", "v2" or "v3"
: ${APP_VERSION:="v1"}

echo "- Deleting application version ${APP_VERSION}"

cd /tmp/k8s-kafka-experiment
kubectl apply -f backend-service/argocd/application/application_version_$APP_VERSION.yaml
FILE="backend-service/argocd/application/application_version_$APP_VERSION.yaml"
if [ -e "$FILE" ]; then
    echo "  - $FILE exists."
    kubectl delete -f backend-service/argocd/application/application_version_$APP_VERSION.yaml -n argocd || true
    kubectl delete -f backend-service/argocd/application/kafka_schemas_$APP_VERSION.yaml -n argocd || true    
else
    echo "  - $FILE does not exist."
fi
