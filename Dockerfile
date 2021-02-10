# Python DEPS

FROM python:3.7-slim as python-base

ADD requirements.txt .
RUN apt-get update -y \
    && apt-get install -y libssl-dev libxml2-dev libxslt1-dev libxmlsec1-openssl gcc pkg-config \
    && apt-get install -y --no-install-recommends --no-install-suggests libxmlsec1-dev libz-dev \
    && pip install -r requirements.txt \
    && pip install uwsgi

# NODE DEPS

FROM node:10.16 as node-deps

WORKDIR /home/node/app

COPY package.json package-lock.json bower.json gulpfile.js /home/node/app/
COPY compair/static/ /home/node/app/compair/static/

RUN mkdir -p compair/templates/static/ \
    && npm install --production --no-optional \
    && node_modules/gulp/bin/gulp.js \
    && node_modules/gulp/bin/gulp.js prod

# Python Application image

FROM python:3.7-slim as python-app

MAINTAINER Pan Luo <pan.luo@ubc.ca>

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /code
ENV DEV 0

WORKDIR /code

COPY --from=python-base /root/.cache /root/.cache
COPY --from=python-base /requirements.txt /code/requirements.txt

RUN apt-get update -y \
    && apt-get install -y libssl-dev libxml2-dev libxslt1-dev libxmlsec1-openssl \
    && apt-get install -y --no-install-recommends --no-install-suggests libxmlsec1-dev libz-dev \
    && pip install -r /code/requirements.txt \
    && pip install uwsgi \
    # see https://github.com/onelogin/python3-saml/issues/82
    && STATIC_DEPS=true pip install lxml==4.6.2 --force-reinstall \
    && rm -rf /root/.cache \
    && rm -rf /var/lib/apt/lists/*

# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
COPY deploy/docker/uwsgi.ini /etc/uwsgi/

COPY deploy/docker/docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

ADD . /code/
# overrite static files from node built deps
COPY --from=node-deps /home/node/app/compair/static/ /code/compair/static/
COPY --from=node-deps /home/node/app/compair/templates/static/ /code/compair/templates/static/

VOLUME ["/code/persistent"]

EXPOSE 3031

CMD ["uwsgi", "--ini", "/etc/uwsgi/uwsgi.ini"]