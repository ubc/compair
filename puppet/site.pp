package {'libffi-dev':
  ensure => present,
}

include git

class {'nodejs':
  manage_package_repo => true,
}

class {'python':
  version    => 'system',
  pip        => true,
  dev        => true,
  virtualenv => true,
  gunicorn   => false,
}

python::virtualenv { '/vagrant':
  ensure       => present,
  version      => 'system',
  requirements => '/vagrant/requirements.txt',
  systempkgs   => true,
  distribute   => false,
  venv_dir     => '/home/vagrant/venv-acj',
  owner        => 'vagrant',
  group        => 'vagrant',
  cwd          => '/vagrant',
  timeout      => 0,
}

$override_options = {
  'mysqld' => {
    'bind_address' => '0.0.0.0',
  }
}
class { '::mysql::server':
  root_password    => 'acjacj',
  restart          => true,
  override_options => $override_options
}

include mysql::client

mysql::db { 'acj':
  user     => 'acj',
  password => 'acjacj',
  host     => '%',
  grant    => ['ALL'],
}

# setup environment vars for db config
file { '/home/vagrant/.bash_profile':
  ensure => present
}

file_line { 'source acj virtual env':
  path => '/home/vagrant/.bash_profile',
  line => '. /home/vagrant/venv-acj/bin/activate'
}

file_line { 'setup Database URL environment variable':
  path => '/home/vagrant/.bash_profile',
  line => 'export DATABASE_URI=mysql+pymysql://acj:acjacj@localhost/acj'
}
