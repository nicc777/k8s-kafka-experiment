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
cat << EOF > /tmp/cm_template.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: __CONFIGMAP_NAME__-python-cm
data:
  main.py: |
    #!/usr/bin/env python3
EOF
mkdir /tmp/code-configmaps
cd /tmp/code-configmaps

echo "  - raw_data_generator"
FILE="/tmp/k8s-kafka-experiment/backend-service/$APP_VERSION/raw_data_generator/main.py"
TARGET="/tmp/code-configmaps/raw-data-generator-cm.yaml"
if [ -e "$FILE" ]; then
    echo "$FILE exists."
    cp -vf /tmp/cm_template.yaml $TARGET
    sed -i "s/__CONFIGMAP_NAME__/raw-data-generator/g" $TARGET
    cat $FILE | sed 's/^/    /' >> $TARGET
    kubectl apply -f $TARGET -n exp
else
    echo "$FILE does not exist."
fi

echo "  - back_end"
FILE="/tmp/k8s-kafka-experiment/backend-service/$APP_VERSION/back_end/main.py"
TARGET="/tmp/code-configmaps/back-end-cm.yaml"
if [ -e "$FILE" ]; then
    echo "$FILE exists."
    cp -vf /tmp/cm_template.yaml $TARGET
    sed -i "s/__CONFIGMAP_NAME__/back-end/g" $TARGET
    cat $FILE | sed 's/^/    /' >> $TARGET
    kubectl apply -f $TARGET -n exp
else
    echo "$FILE does not exist."
fi

echo "  - back_end_aggregator_producer"
FILE="/tmp/k8s-kafka-experiment/backend-service/$APP_VERSION/back_end_aggregator_producer/main.py"
TARGET="/tmp/code-configmaps/back-end-aggregator-producer-cm.yaml"
if [ -e "$FILE" ]; then
    echo "$FILE exists."
    cp -vf /tmp/cm_template.yaml $TARGET
    sed -i "s/__CONFIGMAP_NAME__/back-end-aggregator-producer/g" $TARGET
    cat $FILE | sed 's/^/    /' >> $TARGET
    kubectl apply -f $TARGET -n exp
else
    echo "$FILE does not exist."
fi

echo "  - front_end_aggregator_consumer"
FILE="/tmp/k8s-kafka-experiment/backend-service/$APP_VERSION/front_end_aggregator_consumer/main.py"
TARGET="/tmp/code-configmaps/front-end-aggregator-consumer-cm.yaml"
if [ -e "$FILE" ]; then
    echo "$FILE exists."
    cp -vf /tmp/cm_template.yaml $TARGET
    sed -i "s/__CONFIGMAP_NAME__/front-end-aggregator-consumer/g" $TARGET
    cat $FILE | sed 's/^/    /' >> $TARGET
    kubectl apply -f $TARGET -n exp
else
    echo "$FILE does not exist."
fi

echo "  - front_end_ui_rest_api"
FILE="/tmp/k8s-kafka-experiment/backend-service/$APP_VERSION/front_end_ui_rest_api/main.py"
TARGET="/tmp/code-configmaps/front-end-ui-rest-api-cm.yaml"
if [ -e "$FILE" ]; then
    echo "$FILE exists."
    cp -vf /tmp/cm_template.yaml $TARGET
    sed -i "s/__CONFIGMAP_NAME__/front-end-ui-rest-api/g" $TARGET
    cat $FILE | sed 's/^/    /' >> $TARGET
    kubectl apply -f $TARGET -n exp
else
    echo "$FILE does not exist."
fi

echo "- Deployment"
APP_VERSION=$APP_VERSION bash /tmp/k8s-kafka-experiment/backend-service/apply_deployments.sh || true

echo "DONE"











