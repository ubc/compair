Deploying ComPAIR on a CentOS 7 Server
=======================================

These instruction are for a fresh CentOS 7 minimal installation. They can be adapted to be used by other unix server installations but may require additional and modified steps. These instructions will help setup MariaDB, NGINX, uWSGI, Redis, and a Celery worker.

Prerequisites
-------------
* Fresh CentOS 7 server with a minimal installation
* root access to server



Setup System
-------------

```
yum -y update
yum -y install curl epel-release
curl --silent --location https://rpm.nodesource.com/setup_7.x | bash -
curl --silent --location https://bootstrap.pypa.io/get-pip.py | python -
yum -y install nodejs mariadb-server git nginx gcc redis python-devel policycoreutils-python xmlsec1-devel bzip2
```

Setup MariaDB
-------------

#### Start MariaDB

```
systemctl enable mariadb
systemctl start mariadb
```

Note: It is highly recommended to run `mysql_secure_installation` to cleanup default installation and change root password

#### Create the compair user and database

```
mysql -u root -p
```

Note: replace the `compair_password` with a secure password.
```
CREATE DATABASE compair;
GRANT ALL ON compair.* TO compair@localhost IDENTIFIED BY 'compair_password';
exit
```

#### Verify that the new account works

```
mysql compair -u compair -p
```

Setup ComPAIR Codebase
-------------

#### Download compair codebase from github

```
mkdir /www_data
cd /www_data
git clone https://github.com/ubc/compair.git
cd compair
```

#### Switch to latest release

```
git checkout vX.X.X
```
Note: please check github for the latest tagged release and replace `vX.X.X` with it

#### Setup virtual environment, python libraries, and javascript libraries

```
pip install virtualenv
virtualenv .env
source .env/bin/activate
make prod
pip install uwsgi
```

Setup Database default data (while still in virtual environment)
-------------

Note: replace `compair_password` with your secure password.
```
DATABASE_URI=mysql+pymysql://compair:compair_password@localhost/compair python manage.py database create
```

Setup Port and File Permissions
-------------

```
semanage port -a -t http_port_t -p tcp 3031
firewall-cmd --permanent --zone=public --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --zone=public --add-port=80/tcp
firewall-cmd --reload
chown nginx:nginx -R /www_data/compair
```

Setup uWSGI
-------------

#### Copy uWSGI config and service

```
mkdir /etc/uwsgi
cp deploy/linux_server/uwsgi.ini /etc/uwsgi/uwsgi.ini
cp deploy/linux_server/compair.service /etc/systemd/system/compair.service
```

Note: Edit `/etc/systemd/system/compair.service` and replace `compair_password` with your secure password.

#### Start uWSGI

```
systemctl start compair
systemctl enable compair
```


Setup NGINX
-------------

### Copy NGINX config

```
cp deploy/linux_server/nginx.conf /etc/nginx/conf.d/default.conf
```

Note: Edit `/etc/nginx/conf.d/default.conf` and replace `SERVER_DOMAIN_OR_IP` with your server's IP address or domain name.

#### Start NGINX

```
systemctl start nginx
systemctl enable nginx
```


Setup Redis
-------------

```
systemctl start redis
systemctl enable redis
```

Setup Celery Worker
-------------

#### Copy Worker service

```
cp deploy/linux_server/worker.service /etc/systemd/system/worker.service
```

Note: Edit `/etc/systemd/system/worker.service` and replace `compair_password` with your secure password.

#### Start Worker

```
systemctl start worker
systemctl enable worker
```

Default admin login
-------------

Once setup is finished, ComPAIR should be accessible with the default admin using username `root` and password `password`.

Maintaining ComPAIR Server
=======================================

Check logs
-------------

* NGINX `/var/log/nginx/compair_error.log` and `/var/log/nginx/compair_access.log`
* uWSGI `/var/log/uwsgi.log`
* Celery Worker `/var/log/worker.log`
* Redis `/var/log/redis/redis.log`
* MariaDB `/var/log/mariadb/mariadb.log`

Maintain Services
-------------

#### After updating a service

```
systemctl daemon-reload
```

#### Start/Stop/Restart NGINX

```
systemctl start nginx
systemctl stop nginx
systemctl reload nginx
```

#### Start/Stop/Restart MariaDB

```
systemctl start mariadb
systemctl stop mariadb
systemctl reload mariadb
```

#### Start/Stop/Restart Redis

```
systemctl start redis
systemctl stop redis
systemctl reload redis
```

#### Start/Stop/Restart ComPAIR

```
systemctl start compair
systemctl stop compair
systemctl reload compair
```

#### Start/Stop/Restart Celery Worker

```
systemctl start worker
systemctl stop worker
systemctl reload worker
```