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


Setting up Learning Analytics
---------------------------

ComPAIR uses the Experience API (xAPI) for collecting learning analytics. xAPI requires a [Learning Record Store (LRS)](http://tincanapi.com/learning-record-store/) to use.
ComPAIR currently only supports basic OAuth1 authentication connections to the LRS. Authentication can be set with either `LRS_USERNAME`+`LRS_PASSWORD` or `LRS_AUTH`.

For development, you can set `LRS_STATEMENT_ENDPOINT` to either the 'local' setting (to dump statements into the `xapi_log` table) or to an account on [https://lrs.adlnet.gov/](https://lrs.adlnet.gov/) for your LRS.
Note that [https://lrs.adlnet.gov/](https://lrs.adlnet.gov/) is set up for testing purposes only and they can clear their data at any time (do not use in production).

### Settings

`XAPI_ENABLED`: Set to 1 to enable collecting learning analytics (disabled by default)

`LRS_STATEMENT_ENDPOINT`: Set the url LRS. Use 'local' for dumping statements into `xapi_log` table ('local' by default)

`LRS_USERNAME`: The username for the OAuth1 account.

`LRS_PASSWORD`: The password for the OAuth1 account.

`LRS_AUTH`: Must be in the format `Basic LRS_USERNAME:LRS_PASSWORD` where `LRS_USERNAME:LRS_PASSWORD` has been base64 encoded.

`XAPI_APP_BASE_URL` Optionally set a base url to use for all statements. This is useful to help keep statement urls consistent if the url of your instance changes over time or is accessible though different routes (ex http+https or multiple sub-domains). (Uses base url of request by default)

xAPI statements require an actor (currently logged in user) account information. The ComPAIR account information will be used by default unless the following settings are changed.

`LRS_ACTOR_ACCOUNT_USE_CAS`: Flag indicating if CAS account information should be used by default if available (disabled by default)

`LRS_ACTOR_ACCOUNT_CAS_HOMEPAGE`: Set the homepage of the CAS account

`LRS_ACTOR_ACCOUNT_CAS_IDENTIFIER`: Optionally set a param to set as the actor's unique key for the CAS account. (uses CAS username by default)

Restart server after making any changes to settings

(Optional) Setting up Background Tasks
---------------------------

### Settings

`CELERY_ALWAYS_EAGER`: Set to 1 to disable background tasks (off by default)

`CELERY_BROKER_URL`: Set the url for the broker tool to be used (ex: redis or rabbitmq instance url)

`CELERY_RESULT_BACKEND`: Set the backend to store results (disabled by default)

Workers will need to be restarted after any changes to them unless the --autoreload option is set (for development only)

if `CELERY_ALWAYS_EAGER` is on, then all background task calls will run locally and block until completed (effectively disabling background tasks).
See the [Celery CELERY_ALWAYS_EAGER docs](http://docs.celeryproject.org/en/latest/configuration.html?highlight=CELERY_BROKER_URL#celery-always-eager).

Restart server after making any changes to settings

User Authentication Settings
---------------------------

### APP Login Settings

`APP_LOGIN_ENABLED`: Enable login via username & password (default: True)

Restart server after making any changes to settings

### CAS Login Settings

`CAS_LOGIN_ENABLED`: Enable login via CAS server (default: True)

`CAS_SERVER`: Url of the CAS Server (do not include trailing slash)

`CAS_AUTH_PREFIX`: Prefix to CAS action (default '/cas')

`CAS_USE_SAML`: Determines which authorization endpoint to use. '/serviceValidate' if false (default). '/samlValidate' if true.

Restart server after making any changes to settings

### LTI Settings

`LTI_LOGIN_ENABLED`: Enable login via LTI consumer (default: True)

Restart server after making any changes to settings

In addition, you must create a LTI consumer key/secret by:
- Logging into ComPAIR as a system administrator
- Clicking on 'Manage LTI' in the header
- Clicking 'Add LTI Consumer'
- Entering a unique key and a hard to guess secret and clicking 'Save'

You can enable/disable consumers from the Manage LTI screen as needed

Disable outgoing https requirements
-----------------------------

`ENFORCE_SSL`: Enforce https on all requests made though LTI and CAS (default: True)

Can be used to disable secure SSL requirements for outgoing and incoming traffic from LTI and CAS.
This should only be used for development or staging purposes.

Google Analytics Web Tracking
-----------------------------
1. Register for a Google Analytics web property ID at http://www.google.ca/analytics/.
2. Set `GA_TRACKING_ID` to your web property id (ex: 'UA-XXXX-Y')

Restart server after making any changes to settings

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