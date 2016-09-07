acj-versus
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

	git clone git@github.com:ubc/acj-versus.git compair
	cd acj && vagrant up

### Start Up the ACJ server

	vagrant ssh -c "cd /vagrant && make rundev"

Now you should be able to open your browser and access ACJ instance using the following address:

	http://localhost:8080/static/index.html#/

### Access Database

A MySQL database is installed and the port 3306 is forwarded to host 3306 (in case there is a conflict, vagrant will pick another port, watch for the information when vagrant starts). From host, database can be connect by:

	mysql -u acj -P 3306 -p acj

The default password is `acjacj`

If you already have a MySQL server running on your host, you may need to use the following command:

	mysql -u acj --protocol=TCP -P 3306 -p acj

Developer Installation - Docker
-------------------------------

### Prerequisites

* [Docker Engine](https://docs.docker.com/engine/installation/)
* [Docker Compose](https://docs.docker.com/compose/install/)

### Clone Repo and Start Server

    git clone git@github.com:ubc/acj-versus.git compair
    docker-compose up -d

After initialization is finished, run the following command if it is the first time:

    docker exec -it compair_app python manage.py database create

ComPAIR is accessible at

    http://localhost:8080/

### Stop Server

    docker-compose stop

### Stop Server and Clean Up

    docker-compose down
    rm -rf .data

### Access Database

    docker exec -it compair_app_1 mysql

### Run Management Command

    docker exec -it compair_app_1 python manage.py COMMAND

### Build Docker Image Locally

    docker build -t ubcctlt/compair-app -f deploy/docker/Dockerfile-dev .

Generate Production Release
---------------------------
Run `gulp prod` to generate the production version. This currently just does two things:
1. Combine all Bower managed javascript libraries into a single minified file.
2. Compile and minify the less files into a single css file.

Database Upgrade
----------------

    vagrant ssh # only for developer installation
    cd /vagrant
    PYTHONPATH=. alembic upgrade head

Google Analytics Web Tracking
-----------------------------
1. Register for a Google Analytics web property ID at http://www.google.ca/analytics/.
2. Create a configuration file under acj/static/tracking.js with the following content:

    ```js
    window.ga=window.ga||function(){(ga.q=ga.q||[]).push(arguments)};ga.l=+new Date;
    ga('create', 'UA-XXXX-Y', 'auto');
    ga('send', 'pageview');
    ```

3. Replace 'UA-XXXX-Y', on the second line, with your web property id.
4. Run `gulp tracking` to include the configuration file.
