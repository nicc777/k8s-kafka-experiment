
- [System Requirements](#system-requirements)
- [Kubernetes Platform for the Lab](#kubernetes-platform-for-the-lab)
  - [k3s](#k3s)
  - [microk8s (old)](#microk8s-old)
- [Ingress](#ingress)

# System Requirements

The lab is running on a Intel Xeon E5-2699 v3 based system with 18 cores and 128 GiB RAM.

The base OS is Debian 12.

On the workstation this repository was cloned on, the following additional software was used:

* BASH (ZSH should be fine as well, but scripts were tested on BASH).
* `jq` (see [homepage](https://jqlang.github.io/jq/))
* Recent version of CLI tools:
  * `kubectl`
  * `helm`
* A fairly recent version of Python 3 (3.10 or later recommended)
* Additional tools that may be helpful:
  * `k9s` ([Homepage](https://k9scli.io/))

It is possible to run everything on a single workstation, provided enough resources is available. 

# Kubernetes Platform for the Lab

## k3s

From 2024-11-30 this lab environment switched to [k3s](https://k3s.io/) in order to move away from Ubuntu snaps.

The Kubernetes version has therefore gone slightly backwards from 1.31 to 1.30.

The installation of `k3s` was done using the basic command (as ROOT):

```shell
# Install k3s without Traefik
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server" sh -s - --disable=traefik

# Use the kubernetes config (you may have to adjust permissions):
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# You may also want to copy the above file to your workstation
# NOTE: You may need to edit the server address to point to your Lab system IP address or hostname
```

Install Traefik as per the "Ingress" section.

You can check `k3s` and `Traefik` is running:

```shell
kubectl get service/traefik -n default
```

Thankfully `k3s` support Helm out of the box, so we can add ArgoCD with the following command:

```shell
kubectl apply -f cicd_base/argocd-k3s.yaml
```

More information can be obtained from the [`k3s` documentation](https://docs.k3s.io/helm).

## microk8s (old)

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

# Ingress

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
* tekton-job.example.tld
* demo.example.tld
* traefik-dashboard.example.tld

