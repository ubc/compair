ComPAIR
==========

[![Join the chat at https://gitter.im/ubc/acj-versus](https://badges.gitter.im/ubc/acj-versus.svg)](https://gitter.im/ubc/acj-versus?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Introduction
------------
ComPAIR is a peer review application developed by the University of British Columbia and freely available for anyone to download, install, and use. ComPAIR distinguishes itself from other peer review tools by harnessing students' innate ability to compare. Rather than have students evaluate one work at a time, ComPAIR presents paired sets of peer work for comparison-based review and feedback.

ComPAIR was inspired by Adaptive Comparative Judgement (ACJ), which is based on the law of comparative judgement conceived by L. L. Thurstone in 1927 that states human beings are better at comparing two things than evaluating one in isolation. In the application, instructors can enable a score for each answer that "adapts" to how the answer does in each comparison. The scores can then be used in generating subsequent pairs, theoretically increasing the similarity in answer quality and the challenge for students in choosing which better meets the instructor-set criteria.

Frameworks
----------
The frontend is purely written in Javascript, using [AngularJS](http://angularjs.org/) as a MVC-framework and [Bootstrap](http://getbootstrap.com/) for the design.
The backend uses the python web application framework [Flask](http://flask.pocoo.org/) with [Flask SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/) for database persistence.
[Alembic](http://alembic.readthedocs.org/) is used to maintain database updates.

Developer Installation - Docker
-------------------------------

### Development Prerequisites

* [Docker Engine](https://docs.docker.com/engine/installation/)
* [Docker Compose](https://docs.docker.com/compose/install/)
* [npm](https://www.npmjs.com/get-npm)

For running unit tests you may also require a `lapack` and `atlas`. These are needed by the python libraries `scipy` and `numpy` to install properly. These can be installed with:

    yum install lapack-devel atlas-devel

or

    apt-get install libatlas-base-dev liblapack-dev

### Clone Repo and Start Server

    git clone git@github.com:ubc/compair.git compair
    cd compair
    npm install
    node_modules/gulp/bin/gulp.js
    node_modules/gulp/bin/gulp.js prod
    docker-compose up -d

After initialization is finished, run the following command if it is the first time:

    docker exec -it compair_app_1 python manage.py database create

Alternatively you can create a pre-populated database with demo data:

    docker exec -it compair_app_1 python manage.py database create -s

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

### Upgrade

    docker-compose down
    docker pull ubcctlt/compair-app # download latest ComPAIR image
    docker-compose up
    docker exec -it compair_app_1 alembic upgrade head # upgrade database

Running tests
---------------------------

### Testing Prerequisites

`libxmlsec1-dev` is an additional system requirement for using `python3-saml`. If you would like to run your tests locally, you need to install it with:

    # brew
    brew install libxmlsec1
    # apt-get
    apt-get install libxmlsec1-dev
    # yum
    yum install xmlsec1-devel

### Python unit tests:

    make testb

Alternatively, these tests may be run inside docker:

    # with compair running via docker-compose, get a shell to the app service
    docker-compose exec app bash
    # run all the backend python tests
    nosetests
    # run individual tests, just use the test import path
    nosetests compair.tests.api.test_assignment.AssignmentAPITests
    # to make the test runner stop on the first failure, add -x
    # to make the test runner capture standard out (for debug prints), add -s
    # combined, this would be
    nosetests -xs

To help debug sqlalchemy, you can tell sqlalchemy to log all generated
statements to stderr by adding this setting to `compair/settings.py`:

    SQLALCHEMY_ECHO = True

### AngularJS spec tests:

    make testf

### AngularJS acceptance tests:

    make testa

These tests are written using Cucumber.js, the tests are located in
`compair/static/test/features/`.

Individual tests can be run by editing `gulpfile.js`. Edit the `bdd` gulp task:

    // original line:
    gulp.src(["compair/static/test/features/*.feature"])
    // comment out original line and set it to a specific feature file, then run
    // make testa
    gulp.src(["compair/static/test/features/view_users.feature"])

Generate Production Release
---------------------------
Run `gulp prod` to generate production assets. This currently just:
1. Combine all Bower managed javascript libraries into a single minified file.
2. Compile and minify the less files into a single css file.
3. Compile and minify the less files used for emails into a single css file in the static folder.
4. Copies all Bower managed images and fonts into the static folder.
5. Copies the pdf viewer copy and assets into the static folder.


Setting up Learning Analytics
---------------------------

ComPAIR uses the Experience API (xAPI) and/or Caliper for collecting learning analytics. Both requires a [Learning Record Store (LRS)](http://tincanapi.com/learning-record-store/) to use.

`LRS_APP_BASE_URL` Optionally set a base url to use for all statements. This is useful to help keep statement urls consistent if the url of your instance changes over time or is accessible though different routes (ex http+https or multiple sub-domains). (Uses base url of request by default)

`LRS_USER_INPUT_FIELD_SIZE_LIMIT`: Set the character limit on statement fields containing user input. Set this in order to prevent sending large statements to the LRS that it can't handle (default: 10,000 characters)

Restart server after making any changes to settings

Statements require an actor (currently logged in user) account information. The ComPAIR account information will be used by default unless the following settings are changed.

### Actor Account settings

Use these settings to control the actor information sent to the LRS. This requires that all users in the system have a globally unique identifier and that the user has an account outside of the system. See [_Global Unique Identifiers_](#global-unique-identifiers) for more information on configuring global unique identifers though different authorization methods.

`LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER`: Flag indicating if `global_unique_identifier` should be used for the actor identifier instead of `uuid`.

`LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE`: Set the actor's homepage when using `global_unique_identifier`.

Note: Both `LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER` and `LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE` need to be configured and the user must have a `global_unique_identifier` or else the default ComPAIR actor will be sent.

##XAPI Setup

ComPAIR currently only supports basic OAuth1 authentication connections to the LRS. Authentication can be set with either `LRS_XAPI_USERNAME`+`LRS_XAPI_PASSWORD` or `LRS_XAPI_AUTH`.

For development, you can set `LRS_XAPI_STATEMENT_ENDPOINT` to either the 'local' setting (to dump statements into the `xapi_log` table) or to an account on [https://lrs.adlnet.gov/](https://lrs.adlnet.gov/) for your LRS.
Note that [https://lrs.adlnet.gov/](https://lrs.adlnet.gov/) is set up for testing purposes only and they can clear their data at any time (do not use in production).

### Settings

`XAPI_ENABLED`: Set to 1 to enable collecting learning analytics (disabled by default)

`LRS_XAPI_STATEMENT_ENDPOINT`: Set the url LRS. Use 'local' for dumping statements into `xapi_log` table ('local' by default)

`LRS_XAPI_USERNAME`: The username for the OAuth1 account.

`LRS_XAPI_PASSWORD`: The password for the OAuth1 account.

`LRS_XAPI_AUTH`: Must be in the format `Basic LRS_XAPI_USERNAME:LRS_XAPI_PASSWORD` where `LRS_XAPI_USERNAME:LRS_XAPI_PASSWORD` has been base64 encoded.

##Caliper Setup

### Settings

`CALIPER_ENABLED`: Set to 1 to enable collecting learning analytics (disabled by default)

`LRS_CALIPER_HOST`: Set the url LRS. Use 'local' for dumping statements into `xapi_log` table ('local' by default)

`LRS_CALIPER_API_KEY`: API key for sending Caliper statements to the LRS.

Setting up Background Tasks
---------------------------

ComPAIR has the following tasks defined under the package `compair.tasks`:

- `reset_demo` - For demo site only.  This task resets the database with default data.
- `update_lti_course_membership` - updates enrollment for the course based on LTI membership
- `update_lti_course_grades` and `update_lti_assignment_grades` - update the course grade and assingment grades respecitvely for LTI consumers
- `send_messages` and `send_message` - send out email messages e.g. students can turn on notification for feedbacks given to their answers
- `set_passwords` - (bulk) updates user passwords e.g. when importing users
- `send_lrs_statement` - sends xAPI statements to Learning Record Store

By default (`CELERY_TASK_ALWAYS_EAGER=1`), these Celery tasks are executed locally by blocking until the task returns. To improve performance, you can configure them as background tasks to run asynchronously.

### Enable tasks to run in background
To run tasks asynchronously, you need to:

- Set up a [Celery broker](http://docs.celeryproject.org/en/latest/getting-started/brokers/) (e.g. Redis, RabbitMQ)
- Set up Celery workers to run the tasks. A worker can be started by running `celery --app=celery_worker.celery worker`. If the work runs in a separate container or virtual machine, remember to apply the same environment variables as the ComPAIR app.
- Set `CELERY_BROKER_URL` according to your broker setup
- Set `CELERY_TASK_ALWAYS_EAGER` to `0` (zero). See below for details
- To add new Celery configuration values, convert the lower case Celery setting into uppercase and prepend it with a `CELERY_` prefix, and then add it to the right overrideable dict in `configuration.py`. E.g.: `broker_url` becomes `CELERY_BROKER_URL`. The setting will be stripped of the `CELERY_` prefix and converted back to lower case via Flask Config's `get_namespace()` before being fed to Celery.
- If worker memory leak is an issue, setting `CELERY_WORKER_MAX_TASKS_PER_CHILD` or `CELERY_WORKER_MAX_MEMORY_PER_CHILD` on the worker can be a workaround.

### Settings

`CELERY_TASK_ALWAYS_EAGER`: Set to `0` to enable background tasks (`1` by default).

`CELERY_BROKER_URL`: Set the url for the broker tool to be used (ex: redis or rabbitmq instance url)

`CELERY_RESULT_BACKEND`: Set the backend to store results (disabled by default)

`CELERY_TIMEZONE`: Set the timezone used for cron jobs. Currently only used for demo installations ('America/Vancouver' by default)

`CELERY_WORKER_MAX_TASKS_PER_CHILD`: Takes an int. Kills a worker process and forks a new one when it has executed the given number of tasks

`CELERY_WORKER_MAX_MEMORY_PER_CHILD`: Takes an int as memory in kilobytes. Kills a worker process and forks a new one when it hits the given memory usage, the currently executing task will be allowed to complete before being killed.

**Restart server after making any changes to settings**

User Authentication Settings
---------------------------

ComPAIR needs at least one of the following authentication settings so that users can log in. You can also enable multiple options at once, e.g., you can use both CAS and LTI.

### APP Login Settings

`APP_LOGIN_ENABLED`: Enable login via username & password (default: True)

Restart server after making any changes to settings

### CAS Login Settings

`CAS_LOGIN_ENABLED`: Enable login via CAS server (default: False)

`CAS_SERVER`: Url of the CAS Server (do not include trailing slash)

`CAS_AUTH_PREFIX`: Prefix to CAS action (default '/cas')

`CAS_USE_SAML`: Determines which authorization endpoint to use. '/serviceValidate' if false (default). '/samlValidate' if true.

`CAS_ATTRIBUTE_USER_ROLE`: CAS field will determine the user's default system role on account creation (default: none). Will only promote to instructor if there is a match against `CAS_INSTRUCTOR_ROLE_VALUES`. If not specified or does not match any value from `CAS_INSTRUCTOR_ROLE_VALUES`, the user will be given the student system role and will manually need to be promoted if needed.

`CAS_INSTRUCTOR_ROLE_VALUES`: List of values `CAS_ATTRIBUTE_USER_ROLE` can contain that would indicate the user is an instructor (default: empty set). Separate values by a space (ex: `instructor teacher staff`).

`CAS_ATTRIBUTE_FIRST_NAME`: Optionally automatically sync user's first name with the supplied CAS attribute (Will only override if attribute is present a contains content).

`CAS_ATTRIBUTE_LAST_NAME`: Optionally automatically sync user's last name with the supplied CAS attribute (Will only override if attribute is present a contains content).

`CAS_ATTRIBUTE_STUDENT_NUMBER`: Optionally automatically sync user's student number with the supplied CAS attribute (Will only override if attribute is present a contains content).

`CAS_ATTRIBUTE_EMAIL`: Optionally automatically sync user's email with the supplied CAS attribute (Will only override if attribute is present a contains content).

Restart server after making any changes to settings

### SAML 2.0 Login Settings

`SAML_LOGIN_ENABLED` Enable login via SAML idp (default: False)

`SAML_SETTINGS` JSON Settings for `python3-saml`

`SAML_SETTINGS_FILE` File location for JSON Settings (only if `SAML_SETTINGS` not used)

`SAML_UNIQUE_IDENTIFIER` Set the attribute that uniquely identifies the user (default: 'uid')

`SAML_METADATA_URL` Optionally load SAML idp metadata by loading the ipd's public metadata.

`SAML_METADATA_ENTITY_ID` Use when loading idp metadata with multiple public entity ids.

`SAML_EXPOSE_METADATA_ENDPOINT` Optionally expose the `/api/saml/metadata` endpoint for the idp's usage (disabled by default).

`SAML_ATTRIBUTE_USER_ROLE`: SAML field will determine the user's default system role on account creation (default: none). Will only promote to instructor if there is a match against `SAML_INSTRUCTOR_ROLE_VALUES`. If not specified or does not match any value from `SAML_INSTRUCTOR_ROLE_VALUES`, the user will be given the student system role and will manually need to be promoted if needed.

`SAML_INSTRUCTOR_ROLE_VALUES`: List of values `SAML_ATTRIBUTE_USER_ROLE` can contain that would indicate the user is an instructor (default: empty set). Separate values by a space (ex: `instructor teacher staff`).

`SAML_ATTRIBUTE_FIRST_NAME`: Optionally automatically sync user's first name with the supplied SAML attribute (Will only override if attribute is present a contains content).

`SAML_ATTRIBUTE_LAST_NAME`: Optionally automatically sync user's last name with the supplied SAML attribute (Will only override if attribute is present a contains content).

`SAML_ATTRIBUTE_STUDENT_NUMBER`: Optionally automatically sync user's student number with the supplied SAML attribute (Will only override if attribute is present a contains content).

`SAML_ATTRIBUTE_EMAIL`: Optionally automatically sync user's email with the supplied SAML attribute (Will only override if attribute is present a contains content).

You must provide `SAML_SETTINGS` or `SAML_SETTINGS_FILE` to use SAML Login. See [python3-saml](https://github.com/onelogin/python3-saml) for details on setting up the JSON settings.
You can use `SAML_METADATA_URL` and `SAML_METADATA_ENTITY_ID` to fetch the idp's public metadata for very request.
You can use `SAML_EXPOSE_METADATA_ENDPOINT` to expose public metadata for the idp.

`libxmlsec1-dev` is an additional system requirement for using `python3-saml`. If you would like to run your tests locally, you can install it with

    # brew
    brew install libxmlsec1
    # apt-get
    apt-get install libxmlsec1-dev
    # yum
    yum install xmlsec1-devel

Note: [https://www.testshib.org](https://www.testshib.org) is used for using saml authentication for development purposes. `deploy/development/dev_saml_settings.json` contains testing settings and should not be used in production. if you edit `dev_saml_settings.json`, you must upload it to [https://www.testshib.org/register.html](https://www.testshib.org/register.html). Please also replace `deploy/development/compair_dev_saml_metadata.xml` with the metadata so it can be kept track of.

### LTI Settings

`LTI_LOGIN_ENABLED`: Enable login via LTI consumer (default: True)
The launch URL will be `https://YOUR_SITE_DOMAIN/api/lti/auth`

Restart server after making any changes to settings

In addition, you must create a LTI consumer key/secret by:
- Logging into ComPAIR as a system administrator
- Clicking on 'Manage LTI' in the header
- Clicking 'Add LTI Consumer'
- Entering a unique key and a hard to guess secret and clicking 'Save'

You can enable/disable consumers from the Manage LTI screen as needed

### Global Unique Identifiers

Useful if your institution has globally unique identifers that are available from the different authorization methods (CAS, SAML, LTI).

Global unique identifers allow ComPAIR to:
- Automatically linking new CAS, SAML, LTI logins to existing accounts associated with the `global_unique_identifier`. The user will not be prompted to login or create a new account.
- Enhance LTI membership service/extension roster syncing by allowing new LTI accounts can be automatically linking to existing ComPAIR accounts or creating new ones (user would no longer be forced to launch an LTI link at least once from the LTI consumer).
- Send learning records to the LRS using `global_unique_identifier` and a different homepage url for the actor account instead of ComPAIR `uuid` and the ComPAIR app url. See [_Actor Account settings_](#actor-account-settings) for more information.

#### CAS

`CAS_GLOBAL_UNIQUE_IDENTIFIER_FIELD`: CAS attribute used to identify an account across third party logins and LTI. Only required when CAS is enabled.

#### SAML

`SAML_GLOBAL_UNIQUE_IDENTIFIER_FIELD`: Optional SAML attribute used to identify an account across third party logins and LTI.

#### LTI

System admins can manage global unique identifiers for each LTI consumer from the 'Manage LTI' screen. Setting the `global_unique_identifier_param` field will use that param to unique identify an account across third party logins and LTI.

Login Screen Customization
---------------------------

Note all html content used for login screen will be [sanitized](https://docs.angularjs.org/api/ngSanitize/service/$sanitize) by AngularJS.

`LOGIN_ADDITIONAL_INSTRUCTIONS_HTML`: Set the text or HTML displayed to users beside the login prompt. By default it will display UBC specific login troubleshooting information (it is recommended to change this value). If left blank, the instruction area will not appear.

`CAS_LOGIN_HTML`: Set the text or HTML displayed to users for selecting to login with CAS (default will be a UBC CWL login button).

`SAML_LOGIN_HTML`: Set the text or HTML displayed to users for selecting to login with SAML (default will be a UBC CWL login button).

(Optional) Email Notification Settings
-----------------------------

Run `gulp prod` in order to generate the combined minified css used in the html emails.

`MAIL_NOTIFICATION_ENABLED`: Enable email notifications application wide (default: False).

Even if notifications are enabled, users can disable them for themselves on the edit account screen.

See [Flask-Mail](https://pythonhosted.org/Flask-Mail/#configuring-flask-mail) for details on configuration settings for mailing notifications.

Disable outgoing https requirements
-----------------------------

`ENFORCE_SSL`: Enforce https on all requests made though LTI and CAS (default: True)

Can be used to disable secure SSL requirements for outgoing and incoming traffic from LTI and CAS.
Note that SAML https settings should be adjusted in `SAML_SETTINGS` or `SAML_SETTINGS_FILE`.
This should only be used for development or staging purposes.

Setup a demo installation
-----------------------------

Demo installations have default data of one course, 2 assignments, 1 instructor, and 30 students. Demo installations do not allow editing/deleting the course, assignments, student answers, or enrollment of any automatic generated default data. Users can still create other courses, assignments, etc and modify them as needed. **Demo installations also allow anyone to create system administrators, instructors, and students at any time.** If the cron job is setup, all data will be automatically reset to defaults every day at 3:00 a.m.

**You should never turn a server with existing data into a demo.** Always delete all existing data first with:

    python manage.py database drop

### Demo Settings

`DEMO_INSTALLATION`: Turns the ComPAIR installation into a demo (default: False)

Setting `DEMO_INSTALLATION` to True will also force `APP_LOGIN_ENABLED` to True and `CAS_LOGIN_ENABLED` to False. `LTI_LOGIN_ENABLED` may still be optionally set to True or False if you want to allow LTI connections to be made to the demo installation.

### Additional Setup

In order for the cron job to work properly, you must also create an additional celery process (ex: `celery -A celery_worker.celery beat`). You should also set `CELERY_TIMEZONE` to your preferred timezone so that the automatic scheduler will reset properly at 3:00 a.m. in your timezone.

You can set the data the first time by running:

    python manage.py database create

Attachments Settings
---------------------------

`ATTACHMENT_UPLOAD_LIMIT`: The file size upload limit (in bytes) for all attachments including Kaltura uploads. (default 250MB).

`ATTACHMENT_ALLOWED_EXTENSIONS`: List of file extensions allowed for upload (default: pdf, mp3, mp4, webm, jpg, jpeg, png). Separate values by a space (ex: `pdf mp3 mp4 webm jpg jpeg png`).

`ATTACHMENT_PREVIEW_EXTENSIONS`: List of file extensions allowed for image preview (default: jpg, jpeg, png). Must also be included in `ATTACHMENT_ALLOWED_EXTENSIONS`. Separate values by a space (ex: `jpg jpeg png`).

Restart server after making any changes to settings

(Optional) Kaltura Media Attachments
---------------------------

You may optionally enable Kaltura uploads to support more media file attachment types with better cross browser playback compatibility.

It is highly recommended to create a separate account for ComPAIR so it does not interfere with other content. You should have a Kaltura player setup and configured for the account.

By Default, ComPAIR treats the account provided as a bucket account to store all video/audio uploads. If global unique identifers are setup, you may alternatively allow users to control their media by turning `KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER` on. This requires that Kaltura user ids use the same global unique identifer.

Currently only version 3 of the Kaltura api is supported.

### Settings

`KALTURA_ENABLED`: Set to 1 to enable uploading media attachments to a Kaltura account (off by default).

`KALTURA_SERVICE_URL`: The base url of the Kaltura server.

`KALTURA_PARTNER_ID`: The partner id of the Kaltura account.

`KALTURA_SECRET`: The secret for the partner id provided.

`KALTURA_USER_ID`: The user id (email) of the Kaltura account.

`KALTURA_PLAYER_ID`: A Kaltura player id (conf ui id) to display the media in.

`KALTURA_VIDEO_EXTENSIONS`: Set of video file extensions that will be uploaded to the Kaltura instead of ComPAIR (default: mp4, mov, and webm). Separate values by a space (ex: `mp4 mov webm`).

`KALTURA_AUDIO_EXTENSIONS`: Set of audio file extensions that will be uploaded to the Kaltura instead of ComPAIR (default: mp3). Separate values by a space (ex: `mp3`).

`KALTURA_USE_GLOBAL_UNIQUE_IDENTIFIER`: Optionally use a user's global unique identifer if available for the Kaltura upload's user_id (off by default). Doing so will allow the user to control their media with Kaltura. Note that it is possible for them to remove the media and it to no longer be available in ComPAIR for comparisons or review.

Restart server after making any changes to settings

Student Data Privacy Settings
-----------------------------

You can control data accessibility for certain sensitive fields with the following settings

`EXPOSE_EMAIL_TO_INSTRUCTOR`: Set to 1 to allow instructors to see and modify email address for students in any of their classes (disabled by default). Instructors can see email info by exporting their class lists or view one of their student's profiles.

`EXPOSE_THIRD_PARTY_USERNAMES_TO_INSTRUCTOR`: Set to 1 to allow instructors to see CAS/SAML usernames for students in any of their classes (disabled by default). Instructors can see CAS?SAML username info by exporting their class lists

In addition you can control if students are able to edit their first name, last name, display name, and student number. System admins and instructors can still modify these profile fields. Any student disabled field for editing will be automatically updated with values from LTI or CAS/SAML on login. Please check the LTI, CAS, or SAML sections for additional environment variables that may need to be included (for example if student number is disabled, then `CAS_ATTRIBUTE_STUDENT_NUMBER` need to be set for automatic updated on student login)

`ALLOW_STUDENT_CHANGE_NAME`: Allows students to edit their first & last names (default: enabled).

`ALLOW_STUDENT_CHANGE_DISPLAY_NAME`: Allows students to edit their display name (default: enabled).

`ALLOW_STUDENT_CHANGE_STUDENT_NUMBER`: Allows students to edit their student number (default: enabled).

`ALLOW_STUDENT_CHANGE_EMAIL`: Allows students to edit their email address (default: enabled).

Google Analytics Web Tracking
-----------------------------
1. Register for a Google Analytics web property ID at http://www.google.ca/analytics/.
2. Set `GA_TRACKING_ID` to your web property id (ex: 'UA-XXXX-Y')

Restart server after making any changes to settings
