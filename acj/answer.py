from acj import app
from general import student, commit
from sqlalchemy_acj import db_session, User, Script, CommentA, CommentQ, Course, Question, ScriptScore
from flask import session, request
from sqlalchemy import desc
import json
import validictory

@app.route('/script/<id>', methods=['GET'])
@student.require(http_exception=401)
def get_script(id):
    query = Script.query.filter_by(id = id).first()
    if not query:
        db_session.rollback()
        return json.dumps({"msg": "No matching script"})
    ret_val = json.dumps( {"content": query.content} )    
    db_session.rollback()
    return ret_val

@app.route('/answer/<id>', methods=['POST'])
@student.require(http_exception=401)
def post_answer(id):
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
        return json.dumps( {"msg": str(error)} )
    qid = id
    user = User.query.filter_by(username = session['username']).first()
    uid = user.id
    author = user.display
    content = param['content']
    table = Script(qid, uid, content)
    db_session.add(table)
    db_session.commit()
    script = Script.query.order_by( Script.time.desc() ).first()
    retval = json.dumps({"id": script.id, "author": author, "time": str(script.time), "content": script.content, "score":"{0:10.2f}".format(0), "avatar": user.avatar, "commentACount": "0"})
    db_session.rollback()
    return retval

@app.route('/answer/<id>', methods=['PUT'])
@student.require(http_exception=401)
def edit_answer(id):
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
    script = Script.query.filter_by(id = id).first()
    script.content = param['content']
    commit()
    return json.dumps({"msg": "PASS"})

@app.route('/answer/<id>', methods=['DELETE'])
@student.require(http_exception=401)
def delete_answer(id):
    script = Script.query.filter_by(id = id).first()
    db_session.delete(script)
    commit()
    return json.dumps({"msg": "PASS"})

@app.route('/ranking/<id>')
@student.require(http_exception=401)
def marked_scripts(id):
    answered = False
    scripts = Script.query.filter_by(qid = id).all()
    slst = []
    for script in scripts:
        author = User.query.filter_by(id = script.uid).first()
        commentA = CommentA.query.filter_by(sid = script.id).all()
        #get the score for each category
        score = ScriptScore.query.filter_by(sid = script.id).order_by(ScriptScore.score.desc()).all()
        scores = []
        for score in score:
            scores.append({"jcid": score.jcid, "score": "{0:10.2f}".format(score.score)})
        slst.append( {"id": script.id, "title": script.title, "author": author.display, "time": str(script.time), "content": script.content, "score": scores, "comments": [], "avatar": author.avatar, "commentACount": len(commentA)} )
        if author.username == session['username']:
            answered = True
        
    question = Question.query.filter_by(id = id).first()
    course = Course.query.filter_by(id = question.cid).first()
    user = User.query.filter_by(username = session['username']).first()
    userQ = User.query.filter_by(id = question.uid).first()
    commentQ = CommentQ.query.filter_by(qid = question.id).all()
    retval = json.dumps( {"display": user.display, "usertype": user.userrole.role, "cid": course.id, "course": course.name, 
                          "qtitle": question.title, "question": question.content, "scripts": slst, "commentQCount": len(commentQ), 
                          "authorQ": userQ.display, "timeQ": str(question.time), "avatarQ": userQ.avatar, "answered": answered,
                          "quiz": question.quiz, "contentLength":question.contentLength} )
    db_session.rollback()
    return retval
