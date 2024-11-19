
- [Kubernetes Platform for the Lab](#kubernetes-platform-for-the-lab)
  - [Ingress](#ingress)

# Kubernetes Platform for the Lab

The experiment is based on a `microk8s` version 1.31 with the following key addons enabled:

* Required:
  * argocd
  * dns
  * hostpath-storage
* Optional, but may be useful
  * dashboard
  * ingress
  * metrics-server
  * registry

Commands on Ubuntu:

```shell
# Install the system
sudo snap install microk8s --classic --channel=1.31

# Export the config for kubectl
microk8s config > ~/kube_conf_microk8s_local.yaml

# Enable the community addons
microk8s enable community 

# Add the required addons
microk8s enable metrics-server storage argocd
```

On you local machine, get the config from the server.

To get the ArgoCD admin password, run:

```shell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## Ingress

Run the following to install Traefik:

```shell
helm upgrade --install -f cicd_base/traefik-values.yaml traefik traefik/traefik
```

> [!NOTE]
> Due to some specific customizations, rather use this way to enable Traefik as apposed to the microk8s Traefik community addon.

To permanently forward common HTTP and HTTPS ports to, run the following (you need two terminals or tmux panels):

```shell
# Make sure you export this in all terminals/panels:
export CLUSTER_ADDRESS=...

# Terminal 1 / Panel 1
export TRAEFIK_INGRESS_NP_HTTP=`kubectl get service/traefik -n default -o json | jq '.spec.ports' | jq '.[] | select(.name=="web")' | jq '.nodePort'`
sudo socat TCP-LISTEN:80,fork,reuseaddr TCP:$CLUSTER_ADDRESS:$TRAEFIK_INGRESS_NP_HTTP

# Terminal 2 / Panel 2
export TRAEFIK_INGRESS_NP_HTTPS=`k get service/traefik -n default -o json | jq '.spec.ports' | jq '.[] | select(.name=="websecure")' | jq '.nodePort'`
sudo socat TCP-LISTEN:443,fork,reuseaddr TCP:$CLUSTER_ADDRESS:$TRAEFIK_INGRESS_NP_HTTPS
```

You can the string `demo.example.tld traefik-dashboard.example.tld` to your `/etc/hosts` file for the host IP 127.0.0.1 - the demo API endpoint will available at this address.

The Traefik dashboard is available at http://traefik-dashboard.example.tld/dashboard/#/

For a complete list of host names for this lab that you can add to your `/ect/hosts` file under the `127.0.0.1`, use the following:

* argocd.example.tld
* kafka-ui.example.tld
* tekton-ui.example.tld
* tekton-iac.example.tld
* tekton-app.example.tld
* demo.example.tld
* traefik-dashboard.example.tld

