#!/bin/bash

sudo apt-get update;
sudo puppet module install puppetlabs-git;
sudo puppet module install puppetlabs-firewall;
sudo puppet module install stankevich-python;
sudo puppet module install puppetlabs-nodejs;
sudo puppet module install puppetlabs-mysql;
sudo puppet module install puppetlabs-apt;
