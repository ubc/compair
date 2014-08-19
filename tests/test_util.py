from acj.core import db
from acj.util import get_model_changes
from data.fixtures import PostsFactory, PostsForQuestionsFactory
from test_acj import ACJTestCase


class DbUtilTests(ACJTestCase):
	def test_get_model_changes(self):
		post = PostsFactory()
		question = PostsForQuestionsFactory()
		question.post = post

		db.session.commit()

		self.assertEqual(get_model_changes(question), None, 'should return None on no change model')

		oldname = question.title
		question.title = 'new title'

		self.assertDictEqual(get_model_changes(question), {'title': {oldname: 'new title'}},
							 'should find the change when attribute changes')

		oldcontent = question.post.content
		question.post.content = "new content"

		self.assertDictEqual(
			get_model_changes(question),
			{'title': {oldname: 'new title'}, 'post': {'content': {oldcontent: 'new content'}}},
			'should find the change when attribute changes')
