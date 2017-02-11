import json

from data.fixtures.test_data import LTITestData, BasicTestData
from compair.tests.test_compair import ComPAIRAPITestCase


class LTIConsumersAPITests(ComPAIRAPITestCase):
    def setUp(self):
        super(LTIConsumersAPITests, self).setUp()
        self.data = BasicTestData()
        self.lti_data = LTITestData()

    def _build_consumer_url(self, consumer_uuid = None):
        return '/api/lti/consumers' + ('/' + consumer_uuid if consumer_uuid else '')

    def test_create_lti_consumer(self):
        url = self._build_consumer_url()

        consumer_expected = {
            'oauth_consumer_key': 'new_consumer_key',
            'oauth_consumer_secret': 'new_consumer_secret'
        }

        # Test login required
        rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
        self.assert401(rv)

        # Test unauthorized access
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
            self.assert403(rv)
        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
            self.assert403(rv)
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
            self.assert403(rv)

        # Test authorized access
        with self.login('root'):
            rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(consumer_expected['oauth_consumer_key'], rv.json['oauth_consumer_key'])
            self.assertEqual(consumer_expected['oauth_consumer_secret'], rv.json['oauth_consumer_secret'])
            self.assertTrue(rv.json['active'])

            # test unique oauth_consumer_key by submitting again
            rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
            self.assertStatus(rv, 409)
            self.assertEqual(rv.json['title'], "Consumer Creation Failed")
            self.assertEqual(rv.json['message'], "A LTI consumer with the same consumer key already exists.")

    def test_list_lti_consumers(self):
        url = self._build_consumer_url()

        # Test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # Test unauthorized access
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)
        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(url)
            self.assert403(rv)
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # Test authorized access
        with self.login('root'):
            lti_consumers = self.lti_data.lti_consumers

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(len(rv.json['objects']), 1)
            self.assertEqual(rv.json['total'], 1)

            for index, lti_consumer in enumerate(lti_consumers):
                self.assertEqual(lti_consumer.oauth_consumer_key, rv.json['objects'][index]['oauth_consumer_key'])
                self.assertEqual(lti_consumer.oauth_consumer_secret, rv.json['objects'][index]['oauth_consumer_secret'])
                self.assertEqual(lti_consumer.active, rv.json['objects'][index]['active'])

            # test paging
            for i in range(1, 30): # add 29 more consumers
                self.lti_data.create_consumer(oauth_consumer_key='lti_consumer_key_'+str(i))
            lti_consumers = self.lti_data.lti_consumers

            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(len(rv.json['objects']), 20)
            self.assertEqual(rv.json['total'], 30)

            for index, lti_consumer in enumerate(lti_consumers[:20]):
                self.assertEqual(lti_consumer.oauth_consumer_key, rv.json['objects'][index]['oauth_consumer_key'])
                self.assertEqual(lti_consumer.oauth_consumer_secret, rv.json['objects'][index]['oauth_consumer_secret'])
                self.assertEqual(lti_consumer.active, rv.json['objects'][index]['active'])

            rv = self.client.get(url+"?page=2")
            self.assert200(rv)
            self.assertEqual(len(rv.json['objects']), 10)
            self.assertEqual(rv.json['total'], 30)

            for index, lti_consumer in enumerate(lti_consumers[20:]):
                self.assertEqual(lti_consumer.oauth_consumer_key, rv.json['objects'][index]['oauth_consumer_key'])
                self.assertEqual(lti_consumer.oauth_consumer_secret, rv.json['objects'][index]['oauth_consumer_secret'])
                self.assertEqual(lti_consumer.active, rv.json['objects'][index]['active'])

            # test order by
            rv = self.client.get(url+"?orderBy=oauth_consumer_secret")
            self.assert200(rv)
            self.assertEqual(len(rv.json['objects']), 20)
            self.assertEqual(rv.json['total'], 30)

            sorted_lti_consumers = sorted(
                [consumer for consumer in lti_consumers],
                key=lambda consumer: consumer.oauth_consumer_secret)[:20]

            for index, lti_consumer in enumerate(sorted_lti_consumers):
                self.assertEqual(lti_consumer.oauth_consumer_key, rv.json['objects'][index]['oauth_consumer_key'])
                self.assertEqual(lti_consumer.oauth_consumer_secret, rv.json['objects'][index]['oauth_consumer_secret'])
                self.assertEqual(lti_consumer.active, rv.json['objects'][index]['active'])

            rv = self.client.get(url+"?orderBy=oauth_consumer_secret&reverse=true")
            self.assert200(rv)
            self.assertEqual(len(rv.json['objects']), 20)
            self.assertEqual(rv.json['total'], 30)

            sorted_lti_consumers = sorted(
                [consumer for consumer in lti_consumers],
                key=lambda consumer: consumer.oauth_consumer_secret,
                reverse=True)[:20]

            for index, lti_consumer in enumerate(sorted_lti_consumers):
                self.assertEqual(lti_consumer.oauth_consumer_key, rv.json['objects'][index]['oauth_consumer_key'])
                self.assertEqual(lti_consumer.oauth_consumer_secret, rv.json['objects'][index]['oauth_consumer_secret'])
                self.assertEqual(lti_consumer.active, rv.json['objects'][index]['active'])

    def test_get_lti_consumer(self):
        lti_consumer = self.lti_data.lti_consumer
        url = self._build_consumer_url(lti_consumer.uuid)

        # Test login required
        rv = self.client.get(url)
        self.assert401(rv)

        # Test unauthorized access
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(url)
            self.assert403(rv)
        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.get(url)
            self.assert403(rv)
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.get(url)
            self.assert403(rv)

        # Test authorized access
        with self.login('root'):
            # invalid id
            rv = self.client.get(self._build_consumer_url("999"))
            self.assert404(rv)

            # valid url
            rv = self.client.get(url)
            self.assert200(rv)
            self.assertEqual(lti_consumer.oauth_consumer_key, rv.json['oauth_consumer_key'])
            self.assertEqual(lti_consumer.oauth_consumer_secret, rv.json['oauth_consumer_secret'])
            self.assertTrue(lti_consumer.active, rv.json['active'])

    def test_edit_lti_consumer(self):
        lti_consumer = self.lti_data.lti_consumer
        url = self._build_consumer_url(lti_consumer.uuid)

        consumer_expected = {
            'id': lti_consumer.uuid,
            'oauth_consumer_key': 'edit_consumer_key',
            'oauth_consumer_secret': 'edit_consumer_secret',
            'active': False
        }

        # Test login required
        rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
        self.assert401(rv)

        # Test unauthorized access
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
            self.assert403(rv)
        with self.login(self.data.get_authorized_ta().username):
            rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
            self.assert403(rv)
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
            self.assert403(rv)

        # Test authorized access
        with self.login('root'):
            # invalid id
            rv = self.client.post(self._build_consumer_url("999"), data=json.dumps(consumer_expected), content_type='application/json')
            self.assert404(rv)

            # invalid id
            invalid_expected = consumer_expected.copy()
            invalid_expected['id'] = "999"
            rv = self.client.post(url, data=json.dumps(invalid_expected), content_type='application/json')
            self.assert400(rv)

            # valid url
            rv = self.client.post(url, data=json.dumps(consumer_expected), content_type='application/json')
            self.assert200(rv)
            self.assertEqual(consumer_expected['oauth_consumer_key'], rv.json['oauth_consumer_key'])
            self.assertEqual(consumer_expected['oauth_consumer_secret'], rv.json['oauth_consumer_secret'])
            self.assertEqual(consumer_expected['active'], rv.json['active'])

            # test edit duplicate consumer key
            lti_consumer2 = self.lti_data.create_consumer()
            url = self._build_consumer_url(lti_consumer2.uuid)

            consumer2_expected = consumer_expected.copy()
            consumer2_expected['id'] = lti_consumer2.uuid

            rv = self.client.post(url, data=json.dumps(consumer2_expected), content_type='application/json')
            self.assertStatus(rv, 409)
            self.assertEqual(rv.json['title'], "Consumer Update Failed")
            self.assertEqual(rv.json['message'], "A LTI consumer with the same consumer key already exists.")

