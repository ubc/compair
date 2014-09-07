.PHONY: docs test

help:
	@echo "  env         create a development environment using virtualenv"
	@echo "  deps        install dependencies using pip"
	@echo "  clean       remove unwanted files like .pyc's"
	@echo "  lint        check style with flake8"
	@echo "  test        run all tests"
	@echo "  testf       run all front end tests"
	@echo "  testb       run all backend tests"

env:
	sudo easy_install pip && \
	pip install virtualenv && \
	virtualenv env && \
	. env/bin/activate && \
	make deps

deps:
	pip install -r requirements.txt
	npm install
	node_modules/.bin/gulp

clean:
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -name '*~' -exec rm -f {} \;
	rm -rf bower_components node_modules

lint:
	flake8 --exclude=env .

testf:
	node_modules/karma/bin/karma start acj/static/test/config/karma.conf.js --single-run

testb:
	python -m unittest discover -s tests/

tdd:
	node_modules/karma/bin/karma start acj/static/test/config/karma.conf.js

test: testf testb

testci:
	node_modules/karma/bin/karma start acj/static/test/config/karma.conf.js --single-run --browsers PhantomJS
	python -m unittest discover -s tests/

run:
	python manage.py runserver -h 0.0.0.0

rundev:
	python manage.py runserver -h 0.0.0.0 -dr
