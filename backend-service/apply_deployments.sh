#!/usr/bin/env bash

cd /tmp/k8s-kafka-experiment
kubectl apply -f backend-service/argocd/application/kafka_topics.yaml -n argocd
FILE="backend-service/argocd/application/application_version_$APP_VERSION.yaml"
if [ -e "$FILE" ]; then
    echo "  - $FILE exists."
    kubectl apply -f backend-service/argocd/application/kafka_schemas_$APP_VERSION.yaml -n argocd || true
    echo "Sleeping 2 minutes"
    sleep `echo $PAUSE_TIME_POST_SCHEMA_DEPLOYMENT | bc`
    kubectl apply -f backend-service/argocd/application/application_version_$APP_VERSION.yaml -n argocd || true
else
    echo "  - $FILE does not exist."
fi

