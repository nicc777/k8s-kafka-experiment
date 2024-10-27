# Preparing and Installing Tekton

The original instructions for Tekton comes from https://tekton.dev/docs/pipelines/install/

In summary, the steps just applied remote YAML files.

Therefore, these steps can be put together in an ArgoCD application in order for Tekton to be deployed by ArgoCD.

## Preparation Steps

Download the YAML files from the URL's in the Tekton documentation.

| Download Link                                                                    | Target File                                                         |
|----------------------------------------------------------------------------------|---------------------------------------------------------------------|
| https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml      | `cicd_base/deployments/tekton/01_tekton_pipeline.yaml`              |
| https://storage.googleapis.com/tekton-releases/triggers/latest/release.yaml      | `cicd_base/deployments/tekton/02_tekton_triggers.yaml`              |
| https://storage.googleapis.com/tekton-releases/triggers/latest/interceptors.yaml | `cicd_base/deployments/tekton/03_tekton_triggets_interceptors.yaml` |

> [!NOTE]
> The order is important and it is further important that a prior steps completely finishes before deploying the next step.

Add the following to all resources:

```yaml
metadata:
  annotations:                              # <-- Add this line
    argocd.argoproj.io/sync-wave: "1"       # <-- Add this line
```

For the first file, use sync wave `1`, for the second `2` and of course for the third `3`.

## Installation

Run the following:

```shell
kubectl apply -f cicd_base/applications/01_tekton.yaml
```

# Prepare Experimental Base Resources

Eun the following:

```shell
kubectl apply -f cicd_base/applications/02_tekton_pipelines.yaml
```

