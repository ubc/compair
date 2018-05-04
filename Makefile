.PHONY: docs test

help:
	@echo "  env         create a development environment using virtualenv"
	@echo "  deps        install dependencies using pip"
	@echo "  clean       remove unwanted files like .pyc's"
	@echo "  lint        check style with flake8"
	@echo "  test        run all tests"
	@echo "  testf       run all front end tests"
	@echo "  testb       run all backend tests"
	@echo "  testa       run all acceptance tests"

env:
	sudo easy_install pip && \
	pip install virtualenv && \
	virtualenv env && \
	. env/bin/activate && \
	make deps

prod:
	$(DOCKERRUN_PY) pip install -r requirements.txt
	$(DOCKERRUN_NODE) npm install
	$(DOCKERRUN_NODE) node_modules/gulp/bin/gulp.js
	$(DOCKERRUN_NODE) node_modules/gulp/bin/gulp.js prod

deps:
	$(DOCKERRUN_PY) pip install -r requirements.txt -r requirements.dev.txt
	$(DOCKERRUN_NODE) npm install
	$(DOCKERRUN_NODE) node_modules/gulp/bin/gulp.js

clean:
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -name '*~' -exec rm -f {} \;
	rm -rf bower_components node_modules
	rm -rf compair/static/dist compair/static/build
	find . -name '__pycache__' -exec rm -fR {} \;

lint:
	flake8 --exclude=env .

testa:
	$(DOCKERRUN_NODE) node_modules/gulp/bin/gulp.js test:acceptance

testf:
	$(DOCKERRUN_NODE) node_modules/gulp/bin/gulp.js test:unit

testb:
	$(DOCKERRUN_PY) nosetests

testb-coverage:
	$(DOCKERRUN_PY) nosetests --with-coverage --cover-package=compair --cover-erase

testb-profile:
	$(DOCKERRUN_PY) nosetests --with-profile

tdd:
	$(DOCKERRUN_NODE) node_modules/karma/bin/karma start compair/static/test/config/karma.conf.js

test: testf testb

testci:
	$(DOCKERRUN_NODE) node_modules/karma/bin/karma start compair/static/test/config/karma.conf.js --single-run --browsers PhantomJS
	$(DOCKERRUN_PY) python -m unittest discover -s compair/tests/

testsauce:
	$(DOCKERRUN_NODE) node_modules/gulp/bin/gulp.js  test:acceptance:sauce

run:
	$(DOCKERRUN_PY) python manage.py runserver -h 0.0.0.0

rundev:
	$(DOCKERRUN_PY) python manage.py runserver -h 0.0.0.0 -dr

docker-image:
	docker build -t ubcctlt/compair-app .
