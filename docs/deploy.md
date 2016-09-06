This page is not up-to-date. Needed to be revised.

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
