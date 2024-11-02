#!/usr/bin/env bash

echo "TEST"
echo "----------------------------------------"
ls -lahrt /tmp || true
echo "----------------------------------------"
ls -lahrt /tmp/k8s-kafka-experiment/backend-service/test.sh || true
echo "----------------------------------------"
kubectl get namespaces || true
echo "----------------------------------------"
echo "COMMAND                           : ${COMMAND}"
echo "APP_VERSION                       : ${APP_VERSION}"
echo "CANARY_CONFIG                     : ${CANARY_CONFIG}"
echo "PAUSE_TIME_POST_SCHEMA_DEPLOYMENT : ${PAUSE_TIME_POST_SCHEMA_DEPLOYMENT}"
echo
echo "sleeping..."
echo
sleep `echo $PAUSE_TIME_POST_SCHEMA_DEPLOYMENT | bc`
echo "----------------------------------------"
echo "TEST DONE"
