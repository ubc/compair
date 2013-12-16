from acj import app
from general import commit
from sqlalchemy_acj import db_session, User, CommentA, CommentQ, CommentJ, Question
from flask import session, request
from sqlalchemy import desc
import json
import validictory

def get_comments(type, id, sidl=None, sidr=None):
	comments = []
	lst = []
	if (type == 'answer'):
		comments = CommentA.query.filter_by(sid = id).order_by( CommentA.time ).all()
	elif (type == 'question'):
		comments = CommentQ.query.filter_by(qid = id).order_by( CommentQ.time ).all()
	elif (type == 'judgement'):
		comments = CommentJ.query.filter_by(qid = id, sidl = sidl, sidr = sidr).order_by( CommentJ.time ).all()
	for comment in comments:
		author = User.query.filter_by(id = comment.uid).first()
		lst.append( {"id": comment.id, "author": author.display, "time": str(comment.time), "content": comment.content, "avatar": author.avatar} )
	if (type == 'question'):
		question = Question.query.filter_by(id = id).first()
	else:
		question = None
    #TODO , "contentLength": "0" if not question else question.contentLength
	retval = json.dumps( {"comments": lst} )
	db_session.rollback()
	return retval

def make_comment(type, id, content, sidl=None, sidr=None):
	table = ''
	uid = User.query.filter_by(username = session['username']).first().id
	if (type == 'answer'):
		table = CommentA(id, uid, content)
	elif (type == 'question'):
		table = CommentQ(id, uid, content)
	elif (type == 'judgement'):
		table = CommentJ(id, sidl, sidr, uid, content)
	db_session.add(table)
	db_session.commit()
	comment = ''
	if (type == 'answer'):
		comment = CommentA.query.order_by( CommentA.time.desc() ).first()
	elif (type == 'question'):
		comment = CommentQ.query.order_by( CommentQ.time.desc() ).first()
	elif (type == 'judgement'):
		comment = CommentJ.query.order_by( CommentJ.time.desc() ).first()
	author = User.query.filter_by(id = comment.uid).first()
	retval = json.dumps({"comment": {"id": comment.id, "author": author.display, "time": str(comment.time), "content": comment.content, "avatar": author.avatar}})
	db_session.rollback()
	return retval

def edit_comment(type, id, content, sidl=None, sidr=None):
	comment = ''
	if (type == 'answer'):
		comment = CommentA.query.filter_by(id = id).first()
	elif (type == 'question'):
		comment = CommentQ.query.filter_by(id = id).first()
	elif (type == 'judgement'):
		comment = CommentJ.query.filter_by(id = id, sidl = sidl, sidr = sidr).first()
	comment.content = content
	db_session.commit()
	db_session.rollback()
	return json.dumps({"msg": "PASS"})

def delete_comment(type, id, sidl=None, sidr=None):
	comment = ''
	if (type == 'answer'):
		comment = CommentA.query.filter_by(id = id).first()
	elif (type == 'question'):
		comment = CommentQ.query.filter_by(id = id).first()
	elif (type == 'judgement'):
		comment = CommentJ.query.filter_by(id = id, sidl = sidl, sidr = sidr).first()
	db_session.delete(comment)
	commit()
	return json.dumps({"msg": "PASS"})


@app.route('/answer/<id>/comment')
def get_commentsA(id):
	return get_comments('answer', id)


@app.route('/answer/<id>/comment', methods=['POST'])
def comment_answer(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return make_comment('answer', id, param['content'])


@app.route('/answer/<id>/comment', methods=['PUT'])
def edit_commentA(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return edit_comment('answer', id, param['content'])


@app.route('/answer/<id>/comment', methods=['DELETE'])
def delete_commentA(id):
	return delete_comment('answer', id)


@app.route('/question/<id>/comment')
def get_commentsQ(id):
	return get_comments('question', id)


@app.route('/question/<id>/comment', methods=['POST'])
def comment_question(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return make_comment('question', id, param['content'])


@app.route('/question/<id>/comment', methods=['PUT'])
def edit_commentQ(id):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return edit_comment('question', id, param['content'])

@app.route('/question/<id>/comment', methods=['DELETE'])
def delete_commentQ(id):
	return delete_comment('question', id)

@app.route('/judgepage/<id>/comment/<sidl>/<sidr>')
def get_commentsJ(id, sidl, sidr):
	return get_comments('judgement', id, sidl, sidr)


@app.route('/judgepage/<id>/comment/<sidl>/<sidr>', methods=['POST'])
def comment_judgement(id, sidl, sidr):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return make_comment('judgement', id, param['content'], sidl, sidr)


@app.route('/judgepage/<id>/comment/<sidl>/<sidr>', methods=['PUT'])
def edit_commentJ(id, sidl, sidr):
	param = request.json
	schema = {
		'type': 'object',
		'properties': {
			'content': {'type': 'string'}
		}
	}
	try:
		validictory.validate(param, schema)
	except ValueError, error:
		print (str(error))
		return json.dumps( {"msg": str(error)} )
	return edit_comment('judgement', id, param['content'], sidl, sidr)


@app.route('/judgepage/<id>/comment/<sidl>/<sidr>', methods=['DELETE'])
def delete_commentJ(id, sidl, sidr):
	return delete_comment('judgement', id, sidl, sidr)
