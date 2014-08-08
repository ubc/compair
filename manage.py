from flask.ext.script import Manager, Server

from acj.manage.database import manager as database_manager
from acj.manage.sample_data import manager as sample_data_manager
from acj import create_app


manager = Manager(create_app)
# register sub-managers
manager.add_command("database", database_manager)
manager.add_command("sampledata", sample_data_manager)
manager.add_command("runserver", Server(port=8080))

if __name__ == "__main__":
	manager.run()
