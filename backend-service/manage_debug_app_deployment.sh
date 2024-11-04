#!/usr/bin/env bash

# Users can define a custom script filename in the VERSION parameter

set -e

# Checkout our projectcd
cd /tmp/k8s-kafka-experiment

# Seelct a script
FILE="backend-service/debug_code_apps/dummy.py"
if [ -e "$VERSION" ]; then
    echo "  - $VERSION exists."
    FILE=$VERSION
else
    echo "  - $VERSION does not exist. Using $FILE"
fi

# Deploy the script as a configmap
echo "- Packaging Configmap's for Python files"
cat << EOF > /tmp/cm_template.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: debug-python-cm
data:
  main.py: |
    #!/usr/bin/env python3
EOF
mkdir /tmp/code-configmaps
TARGET="/tmp/code-cm.yaml"
cp -vf /tmp/cm_template.yaml $TARGET
cat $FILE | sed 's/^/    /' >> $TARGET


if [ -z "${MODE}" ]; then
  echo "MODE is not set."
else
  echo "MODE is set to ${MODE}."
  case "${MODE}" in
    "DEPLOY")
      echo "Applying debug-code config map"
      kubectl apply -f $TARGET -n exp
      echo "Applying debug-app APplication in ArgoCD"
      kubectl apply -f backend-service/argocd/application/debug_app.yaml -n argocd
      echo "DONE with all deployments of the debug-app components"
      ;;
    "DELETE")
      echo "Deleting debug-app Application from ArgoCD"
      kubectl delete -f backend-service/argocd/application/debug_app.yaml -n argocd
      echo "Next: deleting the code config map"
      kubectl delete -f $TARGET -n exp
      echo "DONE deleteing"
      ;;
    *)
      echo "Unknown value: ${MODE}"
      ;;
  esac
fi


