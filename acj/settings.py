import os


def load_setting(default, env_list):
    value = default
    for env in env_list:
        value = os.environ.get(env, value)
    return value


DATABASE = {'drivername': 'mysql',
            'host': load_setting('localhost', ['OPENSHIFT_MYSQL_DB_HOST']),
            'port': load_setting('3306', ['OPENSHIFT_MYSQL_DB_PORT']),
            'username': load_setting('acj', ['OPENSHIFT_MYSQL_DB_USERNAME']),
            'password': load_setting('acj', ['OPENSHIFT_MYSQL_DB_PASSWORD']),
            'database': load_setting('acj', ['OPENSHIFT_GEAR_NAME']),
            }

DATABASE_TEST = {'drivername': 'mysql',
                 'host': 'localhost',
                 'port': '3306',
                 'username': 'acj',
                 'password': '',
                 'database': 'acj_test'}
