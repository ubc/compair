from __future__ import division
from acj import app
from general import student, commit
from sqlalchemy_acj import db_session, User, Course, Question, CommentJ, Judgement, Enrollment, Script, JudgementCategory, JudgementWinner, ScriptScore
from sqlalchemy import func
from random import shuffle
from flask import session, request
import json

def estimate_score(id, winners):
    #get all scripts in that question
    scripts = Script.query.filter_by(qid = id).order_by( Script.id ).all()
    for script in scripts:
        #check if the script has received scores for all categories yet, if not add it to the table
        for winner in winners:
            scriptTmp = ScriptScore.query.filter_by(sid = script.id).filter_by(jcid = winner['jcid']).first()
            if not scriptTmp:
                scriptTmp = ScriptScore(script.id, winner['jcid'], 0, 0)
                db_session.add(scriptTmp)
    db_session.commit()
    #recalculate the scores
    for winner in winners:
        for scriptsl in scripts:
            scriptl = ScriptScore.query.filter_by(sid = scriptsl.id).filter_by(jcid = winner['jcid']).first()
            sidl = scriptl.id
            sigma = 0
            lwins = scriptl.wins
            for scriptsr in scripts:
                scriptr = ScriptScore.query.filter_by(sid = scriptsr.id).filter_by(jcid = winner['jcid']).first()
                if scriptl != scriptr:
                    rwins = scriptr.wins
                    if lwins + rwins == 0:
                        prob = 0
                    else:
                        prob = lwins / (lwins + rwins)
                    sigma = sigma + prob
            scriptl.score = sigma
    db_session.commit()
    return '101010100010110'

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
    cats = []
    judgement = Judgement.query.filter(Judgement.script1.has(qid = qid)).group_by(Judgement.sidl, Judgement.sidr).all()
    #.add_columns(func.sum(Judgement.winner == Judgement.sidl, type_=None).label('wins_l'), func.sum(Judgement.winner == Judgement.sidr, type_=None).label('wins_r')).all()
    question = Question.query.filter_by(id = qid).first()
    userQ = User.query.filter_by(id = question.uid).first()
    course = Course.query.filter_by(id = question.cid).first()
    
    winCount = {}
    for row in judgement:
        win = JudgementWinner.query.filter_by(jid = row.id).first()
        winl = 0
        winr = 0
        if win:
            if win.winner == row.sidl:
                winl = 1
            else:
                winr = 1
        if str(row.sidl)+"-"+str(row.sidr) not in winCount:
            winCount[str(row.sidl)+"-"+str(row.sidr)] = {"winsl": winl, "winsr": winr}
        else:
             winCount[str(row.sidl)+"-"+str(row.sidr)] = {"winsl": winner[str(row.sidl)+"-"+str(row.sidr)].winsl + winsl, "winsr": winner[str(row.sidl)+"-"+str(row.sidr)].winsr + winsr}

    categories = JudgementCategory.query.filter_by(cid = question.cid).all()
    
    for cat in categories:
        cats.append({"id": cat.id, "name": cat.name})
    
    for row in judgement:
        winners = {}
        for cat in categories:
            win = JudgementWinner.query.filter_by(jid = row.id).filter_by(jcid = cat.id).first()
            if win:
                winners[cat.id] = win.winner
        user1 = User.query.filter_by(id = row.script1.uid).first()
        user2 = User.query.filter_by(id = row.script2.uid).first()
        commentsCount = CommentJ.query.filter_by(sidl = row.sidl).filter_by(sidr = row.sidr).count()
        
        score = ScriptScore.query.filter_by(sid = row.script1.id).order_by(ScriptScore.score.desc()).all()
        scoresl = []
        for score in score:
            scoresl.append({"jcid": score.jcid, "score": "{0:10.2f}".format(score.score)})
        score = ScriptScore.query.filter_by(sid = row.script2.id).order_by(ScriptScore.score.desc()).all()
        scoresr = []
        for score in score:
            scoresr.append({"jcid": score.jcid, "score": "{0:10.2f}".format(score.score)})
            
        judgements.append({"scriptl": row.script1.content, "scriptr": row.script2.content, "winner":  winCount[str(row.sidl)+"-"+str(row.sidr)], "winners": winners,
                           "sidl": row.sidl, "sidr": row.sidr, "scorel": scoresl, "scorer": scoresr, 
                           "authorl": user1.display, "authorr": user2.display, "timel": str(row.script1.time), "timer": str(row.script2.time), 
                           "avatarl": user1.avatar, "avatarr": user2.avatar, "qid": row.script1.qid, "commentsCount": commentsCount})
    ret_val = json.dumps({"judgements": judgements, "title": question.title, "question": question.content, "cid": course.id, "course": course.name,
                          "authorQ": userQ.display, "timeQ": str(question.time), "avatarQ": userQ.avatar, "categories": cats})
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
    critList = []
    categories = JudgementCategory.query.filter_by(cid = question.cid).all()
    if not categories:
        category = JudgementCategory(course.id, "Which is Better?")
        db_session.add(category)
        db_session.commit()
        critList.append({"id": category.id, "name": category.name})
    for crit in categories:
        critList.append({"id": crit.id, "name": crit.name})
    retval = json.dumps( {"cid": course.id, "course": course.name, "categories": critList, "question": question.content, "qtitle": question.title, "sidl": fresh[0], "sidr": fresh[1]} )
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
        if user.userrole.role != 'Admin':
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

@app.route('/script/<id>', methods=['POST'])
@student.require(http_exception=401)
def mark_script(id):
    param = request.json
    sidl = param['sidl']
    sidr = param['sidr']
    query = User.query.filter_by(username = session['username']).first()
    uid = query.id
    if sidl > sidr:
        temp = sidr
        sidr = sidl
        sidl = temp
        
    #TODO winner is not needed in judgement tab anymore
    judgement = Judgement(uid, sidl, sidr, id)
    db_session.add(judgement)
    commit()
    winners = param['winner']
    for winner in winners:
        judgementwinner = JudgementWinner(judgement.id, winner['jcid'], winner['winner'])
        db_session.add(judgementwinner)
        db_session.commit()
        
        #add or update the winning script
        query = ScriptScore.query.filter_by(sid = winner['winner']).filter_by(jcid = winner['jcid']).first()
        if not query:
            query = ScriptScore(winner['winner'], winner['jcid'], 0, 0)
            db_session.add(query)
        query.wins = query.wins + 1
        query.count = query.count + 1
        db_session.commit()
        #add or update the losing script
        sid = 0
        if sidl == int(winner['winner']):
            sid = sidr
        elif sidr == int(winner['winner']):
            sid = sidl
        query = ScriptScore.query.filter_by(sid = sid).filter_by(jcid = winner['jcid']).first()
        if not query:
            query = ScriptScore(sid, winner['jcid'], 0, 0)
            db_session.add(query)
        query.count = query.count + 1
        db_session.commit()
    
    db_session.commit()
    #calculate the new scores for all scripts in that question
    query = Script.query.filter_by(id = sidl).first()
    estimate_score(query.qid, winners)
        
    return json.dumps({"msg": "Script & Judgement updated"})
