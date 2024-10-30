#!/usr/bin/env bash

cd /tmp/k8s-kafka-experiment/backend-service
kubectl apply -f backend-service/argocd/application/application_version_$APP_VERSION.yaml
FILE="backend-service/argocd/application/application_version_$APP_VERSION.yaml"
if [ -e "$FILE" ]; then
    echo "  - $FILE exists."
    kubectl apply -f backend-service/argocd/application/application_version_$APP_VERSION.yaml -n argocd || true
else
    echo "  - $FILE does not exist."
fi

