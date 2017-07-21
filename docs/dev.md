How to Contribute
=================

Coding Standard
---------------

The code should follow [PEP8](https://www.python.org/dev/peps/pep-0008‎) coding standard.

#### Indentation
This project uses 4 spaces for the indentation.

Testing
-------

### All Tests

    make test

### Backend Testing

    make testb

### Frondend Testing

    make testf

The front end unit tests are located along with the module files instead of in unit test own directory. The files are named as MODULE-NAME_test.js. This convention is based on

    https://docs.google.com/document/d/1XXMvReO8-Awi1EZXAXS4PzDzdNvV6pGcuaF4Q9821Es/pub

### Test Driven Development

    make tdd

This will start a Karma server, which will monitor the js files. If any file is changed, the front end test suite will run. In case something is broken by code change, you will be notified right away.

Dependency Details
------------------

Install all dependencies:

    make deps

Install all the python dependencies (`requirements.txt`):

    pip install -r /path/to/requirements.txt

Install the node dependencies (`package.json`):

    npm install

Install the front-end javascript dependencies (`bower.json`):

    node_modules/.bin/gulp

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

Each page and route should be in their own modules. The primary Javascript import should be named `<module name>-module.js`. The primary template for the module should be named `<module name>-partial.html`. Directives should be named `<directive name>-directive.js`.

Common code shared across many modules in the application should be abstracted out into it's own module and placed in `static/modules/common`.

Dev Notes
-----------

Breadcrumbs are taken care of by [ng-breadcrumbs](https://github.com/ianwalter/ng-breadcrumbs).

Loading indicators are automatically shown by [angular-loading-bar](http://chieffancypants.github.io/angular-loading-bar/).

Toasts/flash messages are provided by [AngularJS-Toaster](https://github.com/jirikavi/AngularJS-Toaster). Customized with success(), error(), etc. methods in the `Toaster` provider, so we don't have to always provide all the params in pop().
