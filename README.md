# tarantula

web server for home projects

### Development

```bash
docker compose up --build dev
```

### Deployment

#### Configure Server

Configuring for Ubuntu Server 24.04

* [Install docker](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) using apt, **not** snap 
* [Configure docker](https://docs.docker.com/engine/install/linux-postinstall/) to run as non-root user
* [Enable docker](https://docker-docs.uclv.cu/engine/install/linux-postinstall/#systemd) to run on start

#### Start Service

```bash
./start.sh
```

* Generate unique cache key for static files from latest commit hash
* Run service in detached mode
* Service will auto-restart due to `restart: always` in `docker-compose.yaml` when server reboots
