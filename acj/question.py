from acj import app
from general import student, commit
from sqlalchemy_acj import db_session, User, Script, Course, Question, Tags
from flask import session, request
from sqlalchemy import desc
import json
import validictory

@app.route('/question/<id>')
@student.require(http_exception=401)
def list_question(id):
    course = Course.query.filter_by(id = id).first()
    questions = Question.query.filter_by(cid = id).order_by( Question.time.desc() ).all()
    lstQuestion = []
    lstQuiz = []
    for question in questions:
        taglistQ = []
        for tag in question.tagsQ:
            taglistQ.append(tag.name)
        author = User.query.filter_by(id = question.uid).first()
        count = Script.query.filter_by(qid = question.id).all()
        if question.quiz:
            user = User.query.filter_by(username = session['username']).first()
            answered = Script.query.filter(Script.qid == question.id).filter(Script.uid == user.id).first()
            lstQuiz.append( {"id": question.id, "author": author.display, "time": str(question.time), "title": question.title, "content": question.content, "avatar": author.avatar, "count": len(count), "answered": answered != None, "tags": taglistQ, "tmptags": taglistQ, "contentLength": course.contentLength} )
        else:
            lstQuestion.append( {"id": question.id, "author": author.display, "time": str(question.time), "title": question.title, "content": question.content, "avatar": author.avatar, "count": len(count), "tags": taglistQ, "tmptags": taglistQ, "contentLength": course.contentLength} )
    taglist = []
    for tag in course.tags:
        taglist.append({"name": tag.name, "id": tag.id})
    db_session.rollback()
    
    return json.dumps( {"course": course.name, "tags": taglist, "questions": lstQuestion, "quizzes": lstQuiz} )

@app.route('/question/<id>', methods=['PUT'])
def edit_question(id):
    param = request.json
    schema = {
        'type': 'object',
        'properties': {
            'title': {'type': 'string'},
            'content': {'type': 'string'},
            'taglist': {'type': 'array'}
        }
    }
    try:
        validictory.validate(param, schema)
    except ValueError, error:
        print (str(error))
        return json.dumps( {"msg": str(error)} )
    question = Question.query.filter_by(id = id).first()
    question.title = param['title']
    question.content = param['content']
    question.tagsQ = []
    for tagname in param['taglist']:
        tag = Tags.query.filter_by(name = tagname).first()
        question.tagsQ.append(tag)
    commit()
    return json.dumps({"msg": "PASS"})

@app.route('/question/<id>', methods=['POST'])
@student.require(http_exception=401)
def create_question(id):
    param = request.json
    schema = {
        'type': 'object',
        'properties': {
            'title': {'type': 'string'},
            'content': {'type': 'string'},
            'type': {'type': 'string'},
            'taglist': {'type': 'array'}
        }
    }
    try:
        validictory.validate(param, schema)
    except ValueError, error:
        print (str(error))
        return json.dumps( {"msg": str(error)} )
    content = param['content']
    title = param['title']
    type = param['type']
    user = User.query.filter_by(username = session['username']).first()
    newQuestion = Question(id, user.id, title, content, type=='quiz')
    db_session.add(newQuestion)
    for id in param['taglist']:
        tag = Tags.query.filter_by(id = id).first()
        newQuestion.tagsQ.append(tag)
    db_session.commit()
    course = Course.query.filter_by(id = id).first()
    retval = json.dumps({"id": newQuestion.id, "author": user.display, "time": str(newQuestion.time), "title": newQuestion.title, "content": newQuestion.content, "avatar": user.avatar, "count": "1" if type=='quiz' else "0", "answered": True})
    db_session.rollback()
    return retval

@app.route('/question/<id>', methods=['DELETE'])
@student.require(http_exception=401)
def delete_question(id):
    question = Question.query.filter_by(id = id).first()
    user = User.query.filter_by(username = session['username']).first()
    if user.id != question.uid and user.userrole.role != 'Teacher' and user.userrole.role != 'Admin':
        retval = json.dumps( {"msg": user.display} )
        db_session.rollback()
        return retval
    db_session.delete(question)
    commit()
    return ''
