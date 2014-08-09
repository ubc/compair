acj-versus
==========

Introduction
------------
Adaptive Comparative Judgement (ACJ) is based on the law of comparative judgement conceived by L. L. Thurstone in 1927 as a method for psychological measurements.
First used for psychological measurements, today it offers an alternative to marking, especially for performance assessments for which achievement can be difficult to describe in mark schemes and for those where inter-marker reliability is often a problem.

This application is based on an updated 2012 paper which details ACJ's method and history.
Students answer questions asked by instructors or other students and are then able to compare and judge the given answers. From these judgements a score for each answer is calculated according to ACJ's methods.


Frameworks
----------
The frontend is purely written in Javascript, using [AngularJS](http://angularjs.org/) as a MVC-framework and [Bootstrap](http://getbootstrap.com/) for the design.
The backend uses the python web application framework [Flask](http://flask.pocoo.org/) with [Flask SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/] for database persistence.
[Alembic] (http://alembic.readthedocs.org/) is used to maintain database updates.


Installation
-----------
The application needs Python v2.6.6 or above and the following Python libraries:
* Flask
* Flask-Principal
* Flask-SQLAlchemy - Can be sped up if when compiled into a Python C extension. Requires the python development headers if compiling the C extension.
* oauth
* passlib
* PIL (Python Imaging Library)
* requests
* validictory

When running on a MySQL database, it also needs Python's MySQL interface.
 
Theoretically it should run on any relational Database, although so far it has only been tested on MySQL.

### Ubuntu Installation
Most of the python libraries are available in the Ubuntu repository: 
`python-flask python-oauth python-passlib python-imaging python-requests python-validictory` 

SQLAlchemy can be sped up by compiling its C extension. This requires `python-dev` to be installed.

Flask-Principal and Flask-SQLAlchemy needs to be installed from PyPI, this can be done with pip, available in the repo as `python-pip`.

MySQL is in the repository under `mysql-server python-mysqldb`.

This results in the following commands:

1. `sudo apt-get install python-dev python-flask python-oauth python-passlib
   python-imaging python-requests python-validictory python-pip mysql-server
   python-mysqldb` 
2. `sudo pip install Flask-Principal`
3. `sudo pip install Flask-SQLAlchemy`

Developer Installation
----------------------

We're testing out using Bower for package management and gulp for build system.

Install the necessary gulp, bower and plugins locally:
	`npm install`

All the dependencies should now be satisfied, we'll now start the build process, which should download all the front-end packages managed by Bower and include them into `index.html`, run:
	`node_modules/.bin/gulp`

Note that we're using the latest version of AngularJS beta (1.3.0), which may have conflicts that require user interaction to resolve. If you get an error about not finding a suitable version Angular, run `bower install` alone, which will let you interactively choose the proper 1.3.0 version. Then run `gulp bowerInstall` and `gulp bowerWiredep` in sequence, which should resolve this.

Partial dependency reference: 
- ng-ckeditor: CKEditor in an Angular directive
- ng-breadcrumbs: Breadcrumb system meant to work with ngRoutes
- angular-http-auth: Watch for http 401 errors reissues pending requests on login
- angular-strap: Bootstrap.js ported from jQuery to Angular

Running the application
-----------------------
Create `config.py` with the proper configurations.

Run the following commands from terminal:

    # install the dependencies
    pip install -r /path/to/requirements.txt
    # create database tables and populate initial data
    python manage.py database create
    # run the server
    python manage.py runserver

Database
--------
###Initial Setup
To create the tables in the database:

    python manage.py database create

Or drop the existing data and recreate the tables:

    python manage.py database recreate

For the full list commands for the database management:

    python manage.py database

For any updates to the database model SQLAlchemy Alembic scripts are used. ([detailed information](http://alembic.readthedocs.org/en/latest/))
###Setting up Alembic
* Setup the environment: `alembic init alembic`
* Set the "sqlalchemy.url" in alembic.ini

###Updating the database schema
* When the application gets updated simply run: `alembic upgrade head`

Conventions
-----------

Each page and route should be in their own modules. The primary Javascript import should be named `<module name>-module.js`. The primary template for the module should be named `<module name>-partial.html`. See `static/modules/example` for an example template that can be used as a base for new modules.

Common code shared across many modules in the application should be abstracted out into it's own module and placed in `static/modules/common`.

Dev Notes
-----------

Breadcrumbs are taken care of by [ng-breadcrumbs](https://github.com/ianwalter/ng-breadcrumbs). 

Loading indicators are automatically shown by [angular-loading-bar](http://chieffancypants.github.io/angular-loading-bar/).

Toasts/flash messages are provided by [AngularJS-Toaster](https://github.com/jirikavi/AngularJS-Toaster). Customized with success(), error(), etc. methods in the `Toaster` provider, so we don't have to always provide all the params in pop().
