import unittest
from acj import create_app
from acj.core import db
from tests import test_app_settings


class ACJTestCase(unittest.TestCase):
	def setUp(self):
		app = create_app(settings_override=test_app_settings)
		self.app = app.test_client()
		db.create_all(app=app)

	def tearDown(self):
		pass

	def test_empty_db(self):
		#rv = self.app.get('/')
		#assert 'No entries here so far' in rv.data
		pass


if __name__ == '__main__':
	unittest.main()