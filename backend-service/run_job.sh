#!/usr/bin/env bash

cd /tmp/k8s-kafka-experiment

echo "- Current directory: ${PWD}"

echo "- Preparing ConfigMap for Job Code"

rm -vf /tmp/cm_template.yaml || true
cat << EOF > /tmp/cm_template.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: __CONFIGMAP_NAME__-job-python-cm
data:
  main.py: |
    #!/usr/bin/env python3
EOF
mkdir /tmp/code-configmaps
cd /tmp/code-configmaps

echo "  - job run"
FILE="/tmp/k8s-kafka-experiment/backend-service/jobs/$JOB_NAME.py"
TARGET="/tmp/code-configmaps/job-cm.yaml"
if [ -e "$FILE" ]; then
    echo "$FILE exists."
    cp -vf /tmp/cm_template.yaml $TARGET
    sed -i "s/__CONFIGMAP_NAME__/$JOB_NAME/g" $TARGET
    cat $FILE | sed 's/^/    /' >> $TARGET
    kubectl apply -f $TARGET -n exp
    kubectl apply -f /tmp/k8s-kafka-experiment/backend-service/jobs/$JOB_NAME.yaml -n exp
    kubectl wait --for=condition=complete job/$JOB_NAME-job -n exp --timeout 120s >/dev/null
    echo "________________________________________"
    kubectl logs job/$JOB_NAME-job -n exp
    echo "________________________________________"
    echo "  - job cleanup"
    kubectl delete -f /tmp/k8s-kafka-experiment/backend-service/jobs/$JOB_NAME.yaml -n exp
    kubectl delete -f $TARGET -n exp
else
    echo "$FILE does not exist."
fi



