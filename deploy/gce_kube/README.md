Deploying ComPAIR on Google Container Engine/Kubernetes
==================================================

This instruction is to deploy the ComPAIR application on Google cloud platform using container engine. Since GCE is using Kubernetes to manage containers, ComPAIR could also be deployed to any Kubernetes cluster using this instruction.


Prerequisites
-------------
* Google Cloud Platform account with billing enabled
* Google Cloud SDK commandline tool - [gcloud](https://cloud.google.com/sdk/). If you can't/don't want to install it, you can use commandline tool provided in Google Cloud Console.
* Google project created. We use `compair-docker`.
* The files in this directory

Setting Up Environment
----------------------
This step is required when you use gcloud on your local environment. If you use commandline tool in Google Cloud Console or your own Kubernetes instance, you can skip to the next step.

### Logging in
```bash
gcloud auth login
```

### Setup Zone
Replace `us-west1-a` with any zone of your preference.

```bash
gcloud config set compute/zone us-west1-a
```

### Set Default Project
```bash
gcloud config set project compair-docker
```

### Installing kubectl
```bash
gcloud components install kubectl
```

### Creating Kubernetes Cluster
The cluster can be customized by adding additional parameters to `clusters create` command, e.g. --machine-type or --num-nodes
```bash
gcloud container clusters create cluster-compair
gcloud container clusters get-credentials cluster-compair
```
Note: Billing needs to be enabled and container engine needs to be initialized by going to container engine page in Google cloud console.

Deploying ComPAIR
---------------

### Setup Auto Persistent Volume Provisioning (GCE and Kube 1.4+ only)
Administrator needs to run the following to enable provisioning for kube 1.4+:
```bash
kubectl create -f gce-pd-storageclass.yaml
```

### Creating Persistent Disk and Volumes
If you are using your own Kubernetes instance, you may want to provision a persistent disk for your database and persistent directory instead of using host path. You might be able to take advantage of auto [persistent volume provisioning](https://github.com/kubernetes/kubernetes/blob/release-1.3/examples/experimental/persistent-volume-provisioning/README.md) if you are using one of the supported storage.

For the cluster on GCE, deployment file used GCE auto provisioning. No need to create disks and volumes manually.

### Creating NFS server and NFS persistent volume(GCE only)
Create NFS server deployment:
```bash
kubectl create -f nfs-deployment.yaml
```

Get NFS service IP, listed under `IP` field:
```
kubectl describe services compair-nfs-server
```
Update the NFS service IP in `persistent-storage.yaml` and then create persistent volume:
```
kubectl create -f persistent-storage.yaml
```

### Setting Up Database Password
Change the password in password.txt. Make sure there is no new line at the end of the file.
```bash
kubectl create secret generic mysql-pass --from-file=password.txt
```

### Creating MySQL Deployment
```bash
kubectl create -f mysql-deployment.yaml
```

### Creating Redis Deployment
```bash
kubectl create -f redis-deployment.yaml
```

### Creating ComPAIR Worker Deployment
```bash
kubectl create -f compair-worker-deployment.yaml
```

### Creating ComPAIR App Deployment
```bash
kubectl create -f compair-deployment.yaml
```

### Getting the Public IP for ComPAIR Service
```bash
kubectl describe services compair
```
The public IP is listed under `LoadBalancer Ingress` field. You may need to wait a little bit for the load balancer getting provisioned.

### Initializing database
```
kubectl exec -it $(kubectl get pods -l app=compair,tier=frontend --no-headers | cut -d " " -f 1) -- ./manage.py database create
```

### Default admin login

Once setup is finished, ComPAIR should be accessible with the default admin using username `root` and password `password`.

Operating ComPAIR Cluster
-----------------------

### Scaling Up/Down
When the load increases, you can scale up your app instances. Change `3` to the number of instances you would like to scale up to.
```bash
kubectl scale deployment/compair --replicas=3
```

Removing ComPAIR From Cluster
---------------------------

```bash
kubectl delete deployment,service -l app=compair
kubectl delete secret mysql-pass
kubectl delete pvc -l app=compair
kubectl delete pv nfs-pv
```

Tearing Down Cluster
--------------------

```bash
gcloud container clusters delete cluster-compair
```
