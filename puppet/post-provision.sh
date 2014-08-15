#!/bin/bash

source /home/vagrant/.bash_profile
cd /vagrant && make deps
python manage.py database create

echo "**************************************"
echo "*       Provision Finished!          *"
echo "**************************************"
