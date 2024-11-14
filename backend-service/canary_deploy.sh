#!/usr/bin/env bash

# "canary_config": "v1:90,v2:10",
# CANARY_CONFIG=v1:90,v2:10

TARGET_1_VERSION=$(echo $CANARY_CONFIG | awk -F, '{print $1}' | awk -F: '{print $1}')
TARGET_1_RATIO=$(echo $CANARY_CONFIG | awk -F, '{print $1}' | awk -F: '{print $2}')
TARGET_2_VERSION=$(echo $CANARY_CONFIG | awk -F, '{print $2}' | awk -F: '{print $1}')
TARGET_2_RATIO=$(echo $CANARY_CONFIG | awk -F, '{print $2}' | awk -F: '{print $2}')

echo
echo "Target 1: "
echo "   Version : ${TARGET_1_VERSION}"
echo "   Ration  : ${TARGET_1_RATIO}"
echo "Target 2: "
echo "   Version : ${TARGET_2_VERSION}"
echo "   Ration  : ${TARGET_2_RATIO}"
echo
echo "Domain     : ${DOMAIN}"
echo
echo "----------------------------------------"


cp -vf backend-service/argocd/application/application_service.yaml /tmp/application_service.yaml
sed -i "s/__VERSION_1__/$TARGET_1_VERSION/g" /tmp/application_service.yaml
sed -i "s/__VERSION_2__/$TARGET_2_VERSION/g" /tmp/application_service.yaml
sed -i "s/__WEIGHT_TARGET_1__/$TARGET_1_RATIO/g" /tmp/application_service.yaml
sed -i "s/__WEIGHT_TARGET_2__/$TARGET_2_RATIO/g" /tmp/application_service.yaml
sed -i "s/__DOMAIN__/$DOMAIN/g" /tmp/application_service.yaml

cat /tmp/application_service.yaml
echo "----------------------------------------"


kubectl apply -f /tmp/application_service.yaml -n argocd

