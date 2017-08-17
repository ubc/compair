Deploying ComPAIR with Docker and Docker-compose
================================================

This instruction uses docker and docker-compose to deploy ComPAIR. This deployment is suitable for deploying ComPAIR onto a single server with minial effort.

The parameters in the template can be changed based on deployment requirement.

Prerequisites
-------------
* Docker Engine 1.12.0+
* Docker-compose 1.12.0+
* ComPAIR source files (used for web container to serve static contents)


Deploying ComPAIR
-----------------

### Deploying

```bash
vi deploy/docker/docker-compose.yml # edit the yaml file to replace the default credentials
docker-compose -f deploy/docker/docker-compose.yml up -d
```

### Initializing App

Once the containers are started, run the follow command to initialize the database:
```
docker exec -it compair_app_1 python manage.py database create
```

Once finished, ComPAIR should be accessible with default user `root`/`password` at `http://localhost/`.

Tearing Down
--------------------

```bash
docker-compose -f deploy/docker/docker-compose.yml down
```

Cleaning Up
-----------
NOTE: This will remove the database and files uploaded by users.

```bash
rm -rf .data
```

Upgrading ComPAIR
-----------------

```bash
docker pull ubcctlt/compair # pull in the latest image
docker-compose -f deploy/docker/docker-compose.yml down
docker-compose -f deploy/docker/docker-compose.yml up
docker exec -it compair_app_1 alembic upgrade head # upgrade database
```