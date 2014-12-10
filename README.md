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

Developer Installation
----------------------

### Install Dependencies

### Vagrant up the VM

	git clone --branch model_refactor git@github.com:ubc/acj-versus.git acj 
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

Generate Production Release
---------------------------
Run `gulp prod` to generate the production version. This currently just does two things: 
1. Combine all Bower managed javascript libraries into a single minified file.
2. Compile and minify the less files into a single css file.

Database Upgrade
----------------

    vagrant ssh # only for developer installation
    cd acj
    PYTHONPATH=. alembic upgrade head

Google Analytics Web Tracking
-----------------------------
1. Register for a Google Analytics web property ID at http://www.google.ca/analytics/.
2. Create a configuration file under acj/static/tracking.js with the following content:

    window.ga=window.ga||function(){(ga.q=ga.q||[]).push(arguments)};ga.l=+new Date;
    ga('create', 'UA-XXXX-Y', 'auto');
    ga('send', 'pageview');

3. Replace 'UA-XXXX-Y', on the second line, with your web property id.
4. Run `gulp tracking` to include the configuration file.