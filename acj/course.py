from acj import app
from general import teacher, student, commit
from sqlalchemy_acj import db_session, User, Script, Course, Question, Enrollment, CommentA, CommentQ, CommentJ, Tags, Judgement
from flask import session, request, Response
from sqlalchemy import func
import json
import validictory

@teacher.require(http_exception=401)
def enrol_users(users, courseId):
    error = []
    success = []
    enrolled = Enrollment.query.filter_by(cid = courseId).with_entities(Enrollment.uid).all()
    enrolled =  [item for sublist in enrolled for item in sublist]
    for u in users:
        if u['user']['id'] in enrolled:
            success.append(u)
            continue
        table = Enrollment(u['user']['id'], courseId)
        db_session.add(table)
        status = commit()
        if status:
            u['eid'] = table.id
            success.append(u)
        else:
            u['msg'] = 'The user is created, but cannot be enrolled'
            error.append(u)
    return {'error': error, 'success': success}


@app.route('/course/<id>', methods=['DELETE'])
def delete_course(id):
    course = Course.query.filter_by( id = id).first()
    db_session.delete(course)
    commit()
    return ''

@app.route('/course', methods=['POST'])
@teacher.require(http_exception=401)
def create_course():
    user = User.query.filter_by( username = session['username']).first()
    param = request.json
    course = Course.query.filter_by( name = param['name']).first()
    if course:
        db_session.rollback()
        return json.dumps( {"flash": 'Course name already exists.'} )
    name = param['name']
    newCourse = Course(name)
    db_session.add(newCourse)
    db_session.commit()
    course = Course.query.filter_by( name = name ).first()
    table = Enrollment(user.id, course.id)
    db_session.add(table)
    retval = json.dumps({"id": newCourse.id, "name": newCourse.name})
    commit()
    return retval

@app.route('/course', methods=['GET'])
@student.require(http_exception=401)
def list_course():
    user = User.query.filter_by( username = session['username'] ).first()
    courses = Course.query.order_by( Course.name ).all()
    lst = []
    for course in courses:
        time = None
        if user.usertype != 'Admin':
            query = Enrollment.query.filter_by(cid = course.id).filter_by(uid = user.id).first()
            if not query:
                continue
            else:
                time = str(query.time)
        new = 0
        if user.lastOnline:
            for question in course.question:
                if question.time > user.lastOnline:
                    new += 1
        else:
            new = len(course.question)
        lst.append( {"id": course.id, "name": course.name, "count": len(course.question), "new": new, "time": time} )
    db_session.rollback()
    return json.dumps( {"courses": lst} )

@app.route('/editcourse/<cid>', methods=['GET'])
@teacher.require(http_exception=401)
def get_course(cid):
    course = Course.query.filter_by(id = cid).first()
    taglist = []
    for tag in course.tags:
        taglist.append({"name": tag.name, "id": tag.id})
    db_session.rollback()
    return json.dumps( {"id": course.id, "name": course.name, "tags": taglist} )

@app.route('/editcourse/<cid>', methods=['PUT'])
@teacher.require(http_exception=401)
def edit_course(cid):
    param = request.json
    schema = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'}
        }
    }
    try:
        validictory.validate(param, schema)
    except ValueError, error:
        print (str(error))
        return json.dumps( {"msg": str(error)} )
    
    course = Course.query.filter_by(id = cid).first()
    course.name = param['name']
    commit()
    
    retval = json.dumps({"msg": "PASS"})
    return retval

@app.route('/managetag', methods=['POST'])
@teacher.require(http_exception=401)
def add_tag():
    param = request.json
    schema = {
        'type': 'object',
        'properties': {
            'cid': {'type': 'integer'},
            'name': {'type': 'string'}
        }
    }
    try:
        validictory.validate(param, schema)
    except ValueError, error:
        print (str(error))
        return json.dumps( {"msg": str(error)} )
    
    course = Course.query.filter_by(id = param['cid']).first()
    tag = Tags.query.filter_by(name = param['name']).first()
    if not tag:
        tag = Tags(param['name'])
    course.tags.append(tag)
    commit()
    
    taglist = []
    for tag in course.tags:
        taglist.append({"name": tag.name, "id": tag.id})
    db_session.rollback()
    return json.dumps( {"id": course.id, "name": course.name, "tags": taglist} )

@app.route('/managetag/<cid>/<tid>', methods=['DELETE'])
@teacher.require(http_exception=401)
def remove_tag(cid, tid):
    param = request.json
    course = Course.query.filter_by(id = cid).first()
    tag = Tags.query.filter_by(id = tid).first()
    course.tags.remove(tag)
    commit()
    
    taglist = []
    for tag in course.tags:
        taglist.append({"name": tag.name, "id": tag.id})
    db_session.rollback()
    return json.dumps( {"id": course.id, "name": course.name, "tags": taglist} )

@app.route('/statistics/<cid>', methods=['GET'])
@teacher.require(http_exception=401)
def get_stats(cid):
    stats = []
    course = Course.query.filter_by(id = cid).first()
    totalQuestionCount = Question.query.filter_by(cid = cid).count()
    totalAnswerCount = Script.query.filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).count()
    studentsInCourse = User.query.join(Enrollment, Enrollment.uid == User.id).filter(Enrollment.cid == cid).filter(User.usertype == 'Student').all()
    for student in studentsInCourse:
        questionCount = Question.query.filter_by(cid = cid).filter_by(uid = student.id).count()
        answerCount = Script.query.filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).filter_by(uid = student.id).count()
        answerAvg = Script.query.with_entities(func.avg(Script.score).label('average')).filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).filter_by(uid = student.id).first()
        stats.append({"totalQuestions": totalQuestionCount, "totalAnswers": totalAnswerCount,"student":{"firstname": student.firstname, "lastname": student.lastname, "questionCount": questionCount, "answerCount": answerCount, "avgScore": answerAvg}})
    return json.dumps({"coursename": course.name, "stats":stats})

@app.route('/statisticexport/', methods=['POST'])
@teacher.require(http_exception=401)
def export_stats():
    params = request.form
    cid = params['cid']
    csv = ''
    comments = ''
    if params['question'] == 'true':
        header = '"author","time","question #"'
        if params['questionTitle'] == 'true':
            header = header + ',"title"'
        if params['questionBody'] == 'true':
            header = header + ',"question"'
        questions = Question.query.filter_by(cid = cid).all()
        csv = '\n"Questions"\n' + header + '\n'
        for row in questions:
            author = User.query.filter_by(id = row.uid).first()
            csv = csv + '"' + author.display + '","' + str(row.time) + '","' + str(row.id) + '",'
            if params['questionTitle'] == 'true':
                csv = csv + '"' + row.title + '",'
            if params['questionBody'] == 'true':
                csv = csv + '"' + row.content + '",'
            csv = csv[:-1] + '\n'
            
            if params['questionComments'] == 'true':
                commentsQ = CommentQ.query.filter_by(qid = row.id).all()
                for c_row in commentsQ:
                    comments = comments + '"' + c_row.content + '"\n'
        if params['questionComments'] == 'true':
            comments = '\n"Question Comments"\n' + comments
            csv = csv + comments
            comments = ''
                    
    if params['answer'] == 'true':
        header = '"author","time","score","question #"'
        if params['answerBody'] == 'true':
            header = header + ',"answer"'
        answers = Script.query.filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).all()
        csv = csv + '\n"Answers"\n' + header + '\n'
        for row in answers:
            author = User.query.filter_by(id = row.uid).first()
            csv = csv + '"' + author.display + '","' + str(row.time) + '","' + str(row.score) + '","' + str(row.qid) + '",'
            if params['answerBody'] == 'true':
                csv = csv + '"' + row.content + '",'
            csv = csv[:-1] + '\n'
            
            if params['answerComments'] == 'true':
                commentsA = CommentA.query.filter_by(sid = row.id).all()
                for c_row in commentsA:
                    comments = comments + '"' + c_row.content + '"\n'
        if params['answerComments'] == 'true':
            comments = '\n"Answer Comments"\n' + comments
            csv = csv + comments
            comments = ''

    if params['judgement'] == 'true':
        header = '"judge","author answer 1","author answer 2","winner"'
        if params['judgementQuestion'] == 'true':
            header = header + ',"title","question"'
        if params['judgementAnswer'] == 'true':
            header = header + ',"answer 1","answer 2","winner"'
        questionsJ = Question.query.with_entities(Question.id).filter_by(cid = cid)
        csv = csv + '\n"Judgements"\n' + header + '\n'
        for question in questionsJ:
            judgements = Judgement.query.filter(Judgement.script1.has(qid = question.id)).all()
            for row in judgements:
                judge = User.query.filter_by(id = row.uid).first()
                author1 = User.query.filter_by(id = row.script1.uid).first()
                author2 = User.query.filter_by(id = row.script2.uid).first()
                if row.winner == row.sidl:
                        winner = "winner: " + author1.display
                else:
                    winner = "winner: " + author2.display
                csv = csv + '"' + judge.display + '","' + author1.display + '","' + author2.display + '","' + winner + '",'
                if params['judgementQuestion'] == 'true':
                    questionsJ = Question.query.filter_by(id = row.script1.qid).all()
                    for rowQ in questionsJ:
                            csv = csv + '"' + rowQ.title + '",' + '"' + rowQ.content + '",'
                if params['judgementAnswer'] == 'true':
                    csv = csv + '"' + row.script1.content + '","' + row.script2.content + '",'
                csv = csv[:-1] + '\n'
                if params['judgementComments'] == 'true':
                    commentsJ = CommentJ.query.filter_by(sidl = row.script1.id).filter_by(sidr = row.script2.id).all()
                    for c_row in commentsJ:
                        comments = comments + c_row.content + '\n'
        if params['judgementComments'] == 'true':
            comments = '\n"Judgement Comments"\n' + comments
            csv = csv + comments
            comments = ''

    return Response(csv, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=statistics.csv"})

@app.route('/enrollment/<cid>')
@teacher.require(http_exception=401)
def students_enrolled(cid):
    users = User.query.filter((User.usertype == 'Teacher') | (User.usertype == 'Student')).order_by( User.fullname ).all()
    studentlst = []
    teacherlst = []
    for user in users:
        enrolled = ''
        query = Enrollment.query.filter_by(uid = user.id).filter_by(cid = cid).first()
        if (query):
            enrolled = query.id
        if user.usertype == 'Student':
            studentlst.append( {"uid": user.id, "username": user.fullname, "enrolled": enrolled} )
        else:
            teacherlst.append( {"uid": user.id, "username": user.fullname, "enrolled": enrolled} )
    course = Course.query.filter_by(id = cid).first()
    retval = json.dumps( { "course": course.name, "students": studentlst, "teachers": teacherlst } )
    db_session.rollback()
    return retval

@app.route('/enrollment/<cid>', methods=['POST'])
@teacher.require(http_exception=401)
def enroll_student(cid):
    user = {'user': {'id': request.json['uid']}}
    retval = enrol_users([user], cid)
    return json.dumps(retval)

@app.route('/enrollment/<eid>', methods=['DELETE'])
@teacher.require(http_exception=401)
def drop_student(eid):
    query = Enrollment.query.filter_by( id = eid ).first()
    db_session.delete(query)
    commit()
    return json.dumps( {"msg": "PASS"} )
