ComPAIR
==========

[![Join the chat at https://gitter.im/ubc/acj-versus](https://badges.gitter.im/ubc/acj-versus.svg)](https://gitter.im/ubc/acj-versus?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Introduction
------------
Adaptive Comparative Judgement (ACJ) is based on the law of comparative judgement conceived by L. L. Thurstone in 1927 as a method for psychological measurements.
First used for psychological measurements, today it offers an alternative to marking, especially for performance assessments for which achievement can be difficult to describe in mark schemes and for those where inter-marker reliability is often a problem.

This application is based on an updated 2012 paper which details ACJ's method and history.
Students answer questions asked by instructors or other students and are then able to compare and judge the given answers. From these comparisons, a score for each answer is calculated according to ACJ's methods.


Frameworks
----------
The frontend is purely written in Javascript, using [AngularJS](http://angularjs.org/) as a MVC-framework and [Bootstrap](http://getbootstrap.com/) for the design.
The backend uses the python web application framework [Flask](http://flask.pocoo.org/) with [Flask SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/) for database persistence.
[Alembic] (http://alembic.readthedocs.org/) is used to maintain database updates.

Developer Installation - VM
---------------------------

### Install Dependencies

### Vagrant up the VM

	git clone git@github.com:ubc/compair.git compair
	cd compair && vagrant up

### Start Up the ComPAIR server

	vagrant ssh -c "cd /vagrant && make rundev"

Now you should be able to open your browser and access ComPAIR instance using the following address:

	http://localhost:8080/static/index.html#/

### Access Database

A MySQL database is installed and the port 3306 is forwarded to host 3306 (in case there is a conflict, vagrant will pick another port, watch for the information when vagrant starts). From host, database can be connect by:

	mysql -u compair -P 3306 -p compair

The default password is `compaircompair`

If you already have a MySQL server running on your host, you may need to use the following command:

	mysql -u compair --protocol=TCP -P 3306 -p compair

### Upgrade Database

    vagrant ssh # only for developer installation
    cd /vagrant
    PYTHONPATH=. alembic upgrade head

Developer Installation - Docker
-------------------------------

### Prerequisites

* [Docker Engine](https://docs.docker.com/engine/installation/)
* [Docker Compose](https://docs.docker.com/compose/install/)

### Clone Repo and Start Server

    git clone git@github.com:ubc/compair.git compair
    docker-compose up -d

After initialization is finished, run the following command if it is the first time:

    docker exec -it compair_app_1 python manage.py database create

ComPAIR is accessible at

    http://localhost:8080/

### Check Logs

    # app
    docker logs -f compair_app_1
    # nginx
    docker logs -f compair_web_1
    # db
    docker logs -f compair_db_1

### Stop Server

    docker-compose stop

### Stop Server and Clean Up

    docker-compose down
    rm -rf .data

### Access Database

    docker exec -it compair_app_1 mysql

### Upgrade Database

    docker exec -it compair_app_1 alembic upgrade head

### Run Management Command

    docker exec -it compair_app_1 python manage.py COMMAND

### Build Docker Image Locally

    docker build -t ubcctlt/compair-app .

Generate Production Release
---------------------------
Run `gulp prod` to generate the production version. This currently just does two things:
1. Combine all Bower managed javascript libraries into a single minified file.
2. Compile and minify the less files into a single css file.


(Optional) Setting up Background Tasks
---------------------------

### Settings

`CELERY_ALWAYS_EAGER`: Set to 1 to disable background tasks (off by default)

`CELERY_BROKER_URL`: Set the url for the broker tool to be used (ex: redis or rabbitmq instance url)

`CELERY_RESULT_BACKEND`: Set the backend to store results (disabled by default)

Workers will need to be restarted after any changes to them unless the --autoreload option is set (for development only)

if `CELERY_ALWAYS_EAGER` is on, then all background task calls will run locally and block until completed (effectively disabling background tasks).
See the [Celery CELERY_ALWAYS_EAGER docs](http://docs.celeryproject.org/en/latest/configuration.html?highlight=CELERY_BROKER_URL#celery-always-eager).

User Authentication Settings
---------------------------

### APP Login Settings

`APP_LOGIN_ENABLED`: Enable login via username & password (default: True)

Restart server after making any changes to settings

### CAS Login Settings

`CAS_LOGIN_ENABLED`: Enable login via CAS server (default: True)

`CAS_ATTRIBUTES_TO_STORE`: Array of CAS attributes to store in the third_party_user table's param column. (default: empty)

See [Flask-CAS](https://github.com/cameronbwhite/Flask-CAS) for other CAS settings

Restart server after making any changes to settings

### LTI Settings

`LTI_LOGIN_ENABLED`: Enable login via LTI consumer (default: True)

In additional, you must manually insert a new LTI consumer record into the lti_consumer table with:
- a unique and valid `oauth_consumer_key` (view the ComPAIRRequestValidator for constraints)
- a valid `oauth_consumer_secret` (view the ComPAIRRequestValidator for constraints)
- `active` set to True

Restart server after making any changes to settings

Disable outgoing https requirements
-----------------------------

`ENFORCE_SSL`: Enforce https on all requests made though LTI and CAS (default: True)

Can be used to disable secure SSL requirements for outgoing and incoming traffic from LTI and CAS.
This should only be used for development purposes only.

Google Analytics Web Tracking
-----------------------------
1. Register for a Google Analytics web property ID at http://www.google.ca/analytics/.
2. Create a configuration file under compair/static/tracking.js with the following content:

    ```js
    window.ga=window.ga||function(){(ga.q=ga.q||[]).push(arguments)};ga.l=+new Date;
    ga('create', 'UA-XXXX-Y', 'auto');
    ga('send', 'pageview');
    ```

3. Replace 'UA-XXXX-Y', on the second line, with your web property id.
4. Run `gulp tracking` to include the configuration file.

Update PDF.js
-------------
The assets for PDF.js are included in the repo and needed to be updated manually when PDF.js is updated.

```
git clone https://github.com/mozilla/pdf.js.git /tmp
cd /tmp/pdf.js
gulp generic
cd -
cp -R /tmp/pdf.js/build/generic/* compair/static/lib_extension/pdfjs
```