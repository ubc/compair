FROM python:2.7

MAINTAINER Pan Luo <pan.luo@ubc.ca>

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /code
ENV DEV 0

RUN easy_install distribute \
    && pip install --no-cache-dir uwsgi \
    && mkdir /code \
    && rm -rf /var/lib/apt/lists/*

# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
COPY deploy/docker/uwsgi.ini /etc/uwsgi/

WORKDIR /code

ADD requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY deploy/docker/docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

ADD . /code/

VOLUME ["/code/persistent"]

EXPOSE 3031

CMD ["uwsgi", "--ini", "/etc/uwsgi/uwsgi.ini"]