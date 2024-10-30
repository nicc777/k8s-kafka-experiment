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
FILE="/tmp/k8s-kafka-experiment/backend-service/backend-service/$APP_VERSION/raw_data_generator/main.py"
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
FILE="/tmp/k8s-kafka-experiment/backend-service/backend-service/$APP_VERSION/back_end/main.py"
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

echo "  - ui"
FILE="/tmp/k8s-kafka-experiment/backend-service/backend-service/$APP_VERSION/ui/main.py"
TARGET="/tmp/code-configmaps/ui-cm.yaml"
if [ -e "$FILE" ]; then
    echo "$FILE exists."
    cp -vf /tmp/cm_template.yaml $TARGET
    sed -i "s/__CONFIGMAP_NAME__/ui/g" $TARGET
    cat $FILE | sed 's/^/    /' >> $TARGET
    kubectl apply -f $TARGET -n exp
else
    echo "$FILE does not exist."
fi

echo "DONE"











