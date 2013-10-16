from acj import app
from general import student
from sqlalchemy_acj import db_session, User, Course, Question, CommentJ, Judgement, Enrollment, Script
from sqlalchemy import func
from random import shuffle
from flask import session
import json


@student.require(http_exception=401)
def get_fresh_pair(scripts, cursidl, cursidr):
    uid = User.query.filter_by(username = session['username']).first().id
    samepair = False
    index = 0
    for scriptl in scripts:
        index = index + 1
        if uid != scriptl.uid:
            for scriptr in scripts[index:]:
                if uid != scriptr.uid:
                    sidl = scriptl.id
                    sidr = scriptr.id
                    if sidl > sidr:
                        temp = sidr
                        sidr = sidl
                        sidl = temp
                    query = Judgement.query.filter_by(uid = uid).filter_by(sidl = sidl).filter_by(sidr = sidr).first()
                    if not query:
                        if sidr == int(cursidr) and sidl == int(cursidl):
                            samepair = True
                            continue
                        db_session.rollback()
                        return [sidl, sidr]
    db_session.rollback()
    if (samepair):
        return 'SAME PAIR'
    return ''

def hi_priority_pool(id, size):
    script = Script.query.filter_by(qid = id).order_by( Script.count.desc() ).first()
    max = script.count
    script = Script.query.filter_by(qid = id).order_by( Script.count ).first()
    min = script.count
    if max == min:
        max = max + 1
    scripts = Script.query.filter_by(qid = id).order_by( Script.count ).limit( size ).all()
    index = 0
    for script in scripts:
        if script.count >= max:
            scripts[:index]
            break
        index = index + 1
    shuffle( scripts )
    return scripts


@app.route('/judgements/<qid>', methods=['GET'])
@student.require(http_exception=401)
def get_judgements(qid):
    judgements = []
    judgement = Judgement.query.filter(Judgement.script1.has(qid = qid)).group_by(Judgement.sidl, Judgement.sidr).add_columns(func.sum(Judgement.winner == Judgement.sidl, type_=None).label('wins_l'), 
                                func.sum(Judgement.winner == Judgement.sidr, type_=None).label('wins_r')).all()
    question = Question.query.filter_by(id = qid).first()
    userQ = User.query.filter_by(id = question.uid).first()
    course = Course.query.filter_by(id = question.cid).first()
    for fullrow in judgement:
        row = fullrow[0]
        user1 = User.query.filter_by(id = row.script1.uid).first()
        user2 = User.query.filter_by(id = row.script2.uid).first()
        commentsCount = CommentJ.query.filter_by(sidl = row.sidl).filter_by(sidr = row.sidr).count()
        judgements.append({"scriptl": row.script1.content, "scriptr": row.script2.content, "winner": row.winner, "wins_l": int(fullrow.wins_l), "wins_r": int(fullrow.wins_r),
                           "sidl": row.sidl, "sidr": row.sidr, "scorel": "{:10.2f}".format(row.script1.score), "scorer": "{:10.2f}".format(row.script2.score), 
                           "authorl": user1.display, "authorr": user2.display, "timel": str(row.script1.time), "timer": str(row.script2.time), 
                           "avatarl": user1.avatar, "avatarr": user2.avatar, "qid": row.script1.qid, "commentsCount": commentsCount})
    ret_val = json.dumps({"judgements": judgements, "title": question.title, "question": question.content, "cid": course.id, "course": course.name,
                          "authorQ": userQ.display, "timeQ": str(question.time), "avatarQ": userQ.avatar})
    db_session.rollback()
    return ret_val

@app.route('/pickscript/<id>/<sl>/<sr>', methods=['GET'])
@student.require(http_exception=401)
def pick_script(id, sl, sr):
    query = hi_priority_pool(id, 10)
    question = Question.query.filter_by(id = id).first()
    course = Course.query.filter_by(id = question.cid).first()
    if not query:
        retval = json.dumps( {"cid": course.id, "course": course.name, "question": question.content} )
        db_session.rollback()
        return retval
    fresh = get_fresh_pair( query, sl, sr )
    if not fresh:
        retval = json.dumps( {"cid": course.id, "question": question.content, "course": course.name} ) 
        db_session.rollback()
        return retval
    if fresh == 'SAME PAIR':
        db_session.rollback()
        return json.dumps( {"nonew": 'No new pair'} )
    retval = json.dumps( {"cid": course.id, "course": course.name, "question": question.content, "qtitle": question.title, "sidl": fresh[0], "sidr": fresh[1]} )
    db_session.rollback()
    return retval

@app.route('/randquestion')
@student.require(http_exception=401)
def random_question():
    scripts = Script.query.order_by( Script.count ).limit(10).all()
    #if not script:
    #    return ''
    #count = script.count
    #scripts = Script.query.filter_by( count = count ).all()
    #while len(scripts) < 2:
    #    count = count + 1
    #    nextscripts = Script.query.filter_by( count = count).all()
    #    scripts.extend( nextscripts )
    user = User.query.filter_by( username = session['username'] ).first()
    shuffle( scripts )
    lowest0 = ''
    retqid = ''
    lowest1 = ''
    for script in scripts:
        if lowest0 == 0:
            break
        qid = script.qid
        question = Question.query.filter_by( id = qid ).first()
        if user.usertype != 'Admin':
            enrolled = Enrollment.query.filter_by( cid = question.cid ).filter_by( uid = user.id ).first()
            if not enrolled:
                continue
            if question.quiz:
                answered = Script.query.filter(Script.qid == qid).filter(Script.uid == user.id).first()
                if not answered:
                    continue
        query = Script.query.filter_by(qid = qid).order_by( Script.count ).limit(10).all()
        shuffle( query )
        fresh = get_fresh_pair( query, 0, 0 )
        if fresh:
            sum = Script.query.filter_by(id = fresh[0]).first().count + Script.query.filter_by(id = fresh[1]).first().count
            if lowest0 == '':
                lowest0 = sum
                retqid = qid
            else:
                lowest1 = sum
                if lowest0 > lowest1:
                    lowest0 = lowest1
                    retqid = qid
    if lowest0 != '':
        retval = json.dumps( {"question": retqid} )
        db_session.rollback()
        return retval
    db_session.rollback()
    return ''