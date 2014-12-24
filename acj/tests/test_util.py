from data.fixtures import PostsFactory, PostsForQuestionsFactory

from acj.core import db
from acj.util import get_model_changes
from acj.tests.test_acj import ACJTestCase


class DbUtilTests(ACJTestCase):
	def test_get_model_changes(self):
		post = PostsFactory()
		question = PostsForQuestionsFactory()
		question.post = post

		db.session.commit()

		self.assertEqual(get_model_changes(question), None, 'should return None on no change model')

		oldname = question.title
		question.title = 'new title'

		self.assertDictEqual(get_model_changes(question), {'title': {'before': oldname, 'after': 'new title'}},
							 'should find the change when attribute changes')

		oldcontent = question.post.content
		question.post.content = "new content"

		self.assertDictEqual(
			get_model_changes(question),
			{'title': {'before': oldname, 'after': 'new title'},
			 'post': {'content': {'before': oldcontent, 'after': 'new content'}}},
			'should find the change when attribute changes')
