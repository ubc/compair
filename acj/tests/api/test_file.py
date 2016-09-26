import mock
from flask import current_app
from flask import make_response

from data.fixtures.test_data import TestFixture
from acj.tests.test_acj import ACJAPITestCase


class FileRetrieveTests(ACJAPITestCase):
    base_url = '/app'
    fixtures = None

    def setUp(self):
        super(FileRetrieveTests, self).setUp()
        self.fixtures = TestFixture().add_course(
            num_students=5, num_assignments=1, num_groups=0,
            num_answers=0, with_draft_student=True)

    def test_get_file(self):
        # test login required
        rv = self.client.get(self.base_url + '/pdf/assignment_1.pdf')
        self.assert401(rv)

        # TODO: no authorization control right now and needs to be added in the future
        # test unauthorized user
        # with self.login(self.fixtures.unauthorized_instructor.username):
        #     rv = self.client.post(self.url)
        #     self.assert403(rv)

        # participation with valid instructor
        with self.login(self.fixtures.instructor.username):
            # invalid file name
            rv = self.client.get(self.base_url + '/pdf/invalid_name.pdf')
            self.assert404(rv)
            self.assertEqual('invalid file name', str(rv.get_data(as_text=True)))

            with mock.patch('acj.os.path.exists', return_value=True):
                with mock.patch('acj.send_file', return_value=make_response("OK")) as mock_send_file:
                    self.client.get(self.base_url + '/pdf/assignment_1.pdf')
                    mock_send_file.assert_called_once_with(
                        '{}/assignment_1.pdf'.format(current_app.config['ATTACHMENT_UPLOAD_FOLDER']),
                        mimetype='application/pdf'
                    )
