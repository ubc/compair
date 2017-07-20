#!/bin/bash
set -eo pipefail

DEV=${DEV:-0}

# if command starts with an option, prepend uwsgi
if [ "${1:0:1}" = '-' ]; then
    set -- uwsgi "$@"
fi

if [ "$1" = 'uwsgi' ]; then
    # append autoreload option
    set -- "$@" --py-autoreload ${DEV}
    if [ $DEV -eq 1 ]
    then
        echo "Running in DEV mode..."
        export FLASK_DEBUG=True
    fi
fi

exec "$@"