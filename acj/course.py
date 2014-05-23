from bouncer.constants import MANAGE, READ, CREATE
from flask import session, request, Response, Blueprint, jsonify
from flask_bouncer import requires, ensure
from flask_login import login_required, current_user
from flask_principal import Identity, identity_changed
import logging
from sqlalchemy import func, cast, DATE, desc, alias, exc
from sqlalchemy.sql import exists
import json
import validictory
import datetime
from decimal import Decimal
from acj.core import db
from acj.models import Courses, UserTypesForCourse, CoursesAndUsers
from acj.util import to_dict, to_dict_paginated

logger = logging.getLogger(__name__)

courses_api = Blueprint('courses_api', __name__)

@courses_api.route('/')
@login_required
@requires(MANAGE, Courses)
def list_course():
	pagination_results = to_dict_paginated(["coursesandusers"], request, Courses.query)
	return jsonify(pagination_results)

@courses_api.route('/', methods=['POST'])
@requires(CREATE, Courses)
def create_course():
	params = request.get_json()
	new_course = Courses(name=params.get("name"), description=params.get("description", None))
	try:
		# create the course
		db.session.add(new_course)
		db.session.commit()
		# also need to enrol the user as an instructor
		instructor_role = UserTypesForCourse.query\
			.filter_by(name = UserTypesForCourse.TYPE_INSTRUCTOR).first()
		new_courseanduser = CoursesAndUsers(
			course = new_course, users_id = current_user.id, usertypeforcourse = instructor_role)
		db.session.add(new_courseanduser)
		db.session.commit()
	except exc.IntegrityError as e:
		db.session.rollback()
		logger.error("Failed to add new course. Duplicate. " + e.message)
		return jsonify({"error":"A course with the same name already exists."}), 400
	except exc.SQLAlchemyError as e:
		db.session.rollback()
		logger.error("Failed to add new course. " + e.message)
		raise
	course_ret = to_dict(new_course, ["coursesandusers"])
	return jsonify(course_ret)

@courses_api.route('/<id>')
@login_required
def get_course(id):
	course = Courses.query.get(id)
	ensure(READ, course)
	course_ret = to_dict(course, ["coursesandusers"])
	return jsonify(course_ret)

#@teacher.require(http_exception=401)
#def enrol_users(users, courseId):
#    error = []
#    success = []
#    enrolled = Enrollment.query.filter_by(cid = courseId).with_entities(Enrollment.uid).all()
#    enrolled =  [item for sublist in enrolled for item in sublist]
#    for u in users:
#        if u['user']['id'] in enrolled:
#            success.append(u)
#            continue
#        usertype = User.query.filter_by(id = u['user']['id']).first().userrole.id
#        table = Enrollment(u['user']['id'], courseId, usertype)
#        db.session.add(table)
#        status = commit()
#        if status:
#            u['eid'] = table.id
#            success.append(u)
#        else:
#            u['msg'] = 'The user is created, but cannot be enrolled'
#            error.append(u)
#    return {'error': error, 'success': success}
#
##wrapper to check if the user has a different role in the course than usually
#@app.route('/editcourse/<cid>', methods=['GET', 'PUT', 'DELETE'])
#@student.require(http_exception=401)
#def manage_course(cid):
#    if "Admin" in session["identity.id"] or "Teacher" in session["identity.id"]:
#        #call the requested method normally
#        if request.method == "GET":
#            return get_course(cid)
#        elif request.method == "PUT":
#            return edit_course(cid)
#        elif request.method == "DELETE":
#            return delete_course(cid)
#    #if not teacher or admin, check if users role is teacher in this course
#    else:
#        userId = User.query.filter_by(username = session['username']).first().id
#        role = Enrollment.query.filter_by(cid = cid).filter_by(uid = userId).first().userrole.role
#        #if it is, change the role temporarily
#        if role == 'Teacher':
#            oldIdentity = session["identity.id"]
#            newIdentity = Identity('only_' + role)
#            #temporarily change the identity
#            identity_changed.send(app, identity=newIdentity)
#            #call the requested method, which will use the changed role
#            if request.method == "GET":
#                response = get_course(cid)
#            elif request.method == "PUT":
#                response = edit_course(cid)
#            elif request.method == "DELETE":
#                response = delete_course(cid)
#            #and change the role back after the call
#            identity_changed.send(app, identity=Identity(oldIdentity))
#            return response
#        #else call the requested method normally
#        elif request.method == "GET":
#            return get_course(cid)
#        elif request.method == "PUT":
#            return edit_course(cid)
#        elif request.method == "DELETE":
#            return delete_course(cid)
#
#@teacher.require(http_exception=401)
#def delete_course(id):
#    course = Course.query.filter_by( id = id).first()
#    db.session.delete(course)
#    commit()
#    return json.dumps( {"flash": 'The course was successfully deleted.'} )
#
#@teacher.require(http_exception=401)
#def edit_course(cid):
#    param = request.json
#    schema = {
#        'type': 'object',
#        'properties': {
#            'name': {'type': 'string'},
#            'contentLength': {'type': 'integer'}
#        }
#    }
#    try:
#        validictory.validate(param, schema)
#    except ValueError, error:
#        print (str(error))
#        return json.dumps( {"msg": str(error)} )
#
#    course = Course.query.filter_by(id = cid).first()
#    course.name = param['name']
#    course.contentLength = param['contentLength']
#    commit()
#
#    retval = json.dumps({"msg": "PASS"})
#    return retval
#
#@app.route('/managecategories', methods=['POST'])
#@student.require(http_exception=401)
#def add_cat():
#    if "Admin" in session["identity.id"] or "Teacher" in session["identity.id"]:
#            return add_categories()
#    else:
#        param = request.json
#        userId = User.query.filter_by(username = session['username']).first().id
#        role = Enrollment.query.filter_by(cid = param['cid']).filter_by(uid = userId).first().userrole.role
#        if role == 'Teacher':
#            oldIdentity = session["identity.id"]
#            newIdentity = Identity('only_' + role)
#            identity_changed.send(app, identity=newIdentity)
#            response = add_categories()
#            identity_changed.send(app, identity=Identity(oldIdentity))
#            return response
#        return add_categories()
#
#@app.route('/managecategories/<cid>/<critid>', methods=['DELETE'])
#@student.require(http_exception=401)
#def remove_cat(cid, critid):
#    if "Admin" in session["identity.id"] or "Teacher" in session["identity.id"]:
#        return remove_categories(cid, critid)
#    else:
#        userId = User.query.filter_by(username = session['username']).first().id
#        role = Enrollment.query.filter_by(cid = cid).filter_by(uid = userId).first().userrole.role
#        if role == 'Teacher':
#            oldIdentity = session["identity.id"]
#            newIdentity = Identity('only_' + role)
#            identity_changed.send(app, identity=newIdentity)
#            response = remove_categories(cid, critid)
#            identity_changed.send(app, identity=Identity(oldIdentity))
#            return response
#        return remove_categories(cid, critid)
#
#@teacher.require(http_exception=401)
#def add_categories():
#    param = request.json
#    schema = {
#        'type': 'object',
#        'properties': {
#            'cid': {'type': 'integer'},
#            'name': {'type': 'string'}
#        }
#    }
#    try:
#        validictory.validate(param, schema)
#    except ValueError, error:
#        print (str(error))
#        return json.dumps( {"msg": str(error)} )
#
#    newCrit = JudgementCategory(param['cid'], param['name'])
#    db.session.add(newCrit)
#    db.session.commit()
#
#    categories = JudgementCategory.query.filter_by(cid = param['cid']).all()
#    critlist = []
#    for crit in categories:
#        critlist.append({"name": crit.name, "id": crit.id})
#    return json.dumps( {"categories": critlist} )
#
#@teacher.require(http_exception=401)
#def remove_categories(cid, critid):
#    param = request.json
#    crit = JudgementCategory.query.filter_by(id = critid).first()
#    db.session.delete(crit)
#    commit()
#
#    categories = JudgementCategory.query.filter_by(cid = cid).all()
#    critlist = []
#    for crit in categories:
#        critlist.append({"name": crit.name, "id": crit.id})
#    return json.dumps( {"categories": critlist} )
#
#@app.route('/managetag', methods=['POST'])
#@student.require(http_exception=401)
#def add_tag():
#    if "Admin" in session["identity.id"] or "Teacher" in session["identity.id"]:
#            return add_tags()
#    else:
#        param = request.json
#        userId = User.query.filter_by(username = session['username']).first().id
#        role = Enrollment.query.filter_by(cid = param['cid']).filter_by(uid = userId).first().userrole.role
#        if role == 'Teacher':
#            oldIdentity = session["identity.id"]
#            newIdentity = Identity('only_' + role)
#            identity_changed.send(app, identity=newIdentity)
#            response = add_tags()
#            identity_changed.send(app, identity=Identity(oldIdentity))
#            return response
#        return add_tags()
#
#@app.route('/managetag/<cid>/<tid>', methods=['DELETE'])
#@student.require(http_exception=401)
#def remove_tag(cid, tid):
#    if "Admin" in session["identity.id"] or "Teacher" in session["identity.id"]:
#        return remove_tags(cid, tid)
#    else:
#        userId = User.query.filter_by(username = session['username']).first().id
#        role = Enrollment.query.filter_by(cid = cid).filter_by(uid = userId).first().userrole.role
#        if role == 'Teacher':
#            oldIdentity = session["identity.id"]
#            newIdentity = Identity('only_' + role)
#            identity_changed.send(app, identity=newIdentity)
#            response = remove_tags(cid, tid)
#            identity_changed.send(app, identity=Identity(oldIdentity))
#            return response
#        return remove_tags(cid, tid)
#
#@teacher.require(http_exception=401)
#def add_tags():
#    param = request.json
#    schema = {
#        'type': 'object',
#        'properties': {
#            'cid': {'type': 'integer'},
#            'name': {'type': 'string'}
#        }
#    }
#    try:
#        validictory.validate(param, schema)
#    except ValueError, error:
#        print (str(error))
#        return json.dumps( {"msg": str(error)} )
#
#    course = Course.query.filter_by(id = param['cid']).first()
#    tag = Tags.query.filter_by(name = param['name']).first()
#    if not tag:
#        tag = Tags(param['name'])
#    course.tags.append(tag)
#    commit()
#
#    taglist = []
#    for tag in course.tags:
#        taglist.append({"name": tag.name, "id": tag.id})
#    db.session.rollback()
#    return json.dumps( {"id": course.id, "name": course.name, "tags": taglist} )
#
#@teacher.require(http_exception=401)
#def remove_tags(cid, tid):
#    param = request.json
#    course = Course.query.filter_by(id = cid).first()
#    tag = Tags.query.filter_by(id = tid).first()
#    course.tags.remove(tag)
#    commit()
#
#    taglist = []
#    for tag in course.tags:
#        taglist.append({"name": tag.name, "id": tag.id})
#    db.session.rollback()
#    return json.dumps( {"id": course.id, "name": course.name, "tags": taglist} )
#
#@app.route('/statistics/<cid>', methods=['GET'])
#@student.require(http_exception=401)
#def get_stat(cid):
#    if "Admin" in session["identity.id"] or "Teacher" in session["identity.id"]:
#        return get_stats(cid)
#    else:
#        userId = User.query.filter_by(username = session['username']).first().id
#        role = Enrollment.query.filter_by(cid = cid).filter_by(uid = userId).first().userrole.role
#        if role == 'Teacher':
#            oldIdentity = session["identity.id"]
#            newIdentity = Identity('only_' + role)
#            identity_changed.send(app, identity=newIdentity)
#            response = get_stats(cid)
#            identity_changed.send(app, identity=Identity(oldIdentity))
#            return response
#        return get_stats(cid)
#
#@teacher.require(http_exception=401)
#def get_stats(cid):
#    stats = []
#    course = Course.query.filter_by(id = cid).first()
#    totalQuestionCount = Question.query.filter_by(cid = cid).count()
#    totalAnswerCount = Script.query.filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).count()
#    studentsInCourse = User.query.join(Enrollment, Enrollment.uid == User.id).join(UserRole).filter(Enrollment.cid == cid).filter(User.userrole.has(UserRole.role == 'Student')).all()
#    for student in studentsInCourse:
#        questionCount = Question.query.filter_by(cid = cid).filter_by(uid = student.id).count()
#        answerCount = Script.query.filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).filter_by(uid = student.id).count()
#
#        answerAvg = ScriptScore.query.with_entities(func.avg(ScriptScore.score).label('average')).filter(ScriptScore.sid.in_(Script.query.with_entities(Script.id).filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).filter_by(uid = student.id))).first()
#
#        pairCount = Judgement.query.filter_by(uid = student.id).filter(Judgement.sidl.in_(Script.query.with_entities(Script.id).filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))))).count()
#        stats.append({"totalQuestions": totalQuestionCount, "totalAnswers": totalAnswerCount,"student":{"firstname": student.firstname, "lastname": student.lastname, "questionCount": questionCount, "answerCount": answerCount, "avgScore": answerAvg, "pairCount": pairCount}})
#    return json.dumps({"coursename": course.name, "stats":stats})
#
#@app.route('/statisticexport/', methods=['POST'])
#@student.require(http_exception=401)
#def export_stat():
#    if "Admin" in session["identity.id"] or "Teacher" in session["identity.id"]:
#        return export_stats(cid)
#    else:
#        params = request.form
#        cid = params['cid']
#        userId = User.query.filter_by(username = session['username']).first().id
#        role = Enrollment.query.filter_by(cid = cid).filter_by(uid = userId).first().userrole.role
#        if role == 'Teacher':
#            oldIdentity = session["identity.id"]
#            newIdentity = Identity('only_' + role)
#            identity_changed.send(app, identity=newIdentity)
#            response = export_stats()
#            identity_changed.send(app, identity=Identity(oldIdentity))
#            return response
#        return export_stats()
#
#@teacher.require(http_exception=401)
#def export_stats():
#    params = request.form
#    cid = params['cid']
#    csv = ''
#    if "startdate" in params:
#        startdate = datetime.datetime.strptime(params['startdate'][0:-24], '%a %b %d %Y')
#        csv = '"Start date","' + str(startdate.date()) + '"\n'
#    if "enddate" in params:
#        enddate = datetime.datetime.strptime(params['enddate'][0:-24], '%a %b %d %Y')
#        #(params['enddate'][0:-15], '%a %b %d %Y %H:%M:%S')
#        csv = csv + '"End date","' + str(enddate.date()) + '"\n'
#    if params['type'] != 'user':
#        comments = ''
#        if params['question'] == 'true':
#            header = '"author","time","question #"'
#            if params['questionTitle'] == 'true':
#                header = header + ',"title"'
#            if params['questionBody'] == 'true':
#                header = header + ',"question"'
#            query = Question.query.filter_by(cid = cid)
#            if "startdate" in params:
#                query = query.filter(cast(Entry.time, DATE) >= startdate)
#            if "enddate" in params:
#                query = query.filter(cast(Entry.time, DATE) <= enddate)
#            questions = query.all()
#            csv = csv + '\n"Questions"\n' + header + '\n'
#            for row in questions:
#                author = User.query.filter_by(id = row.uid).first()
#                csv = csv + '"' + author.display + '","' + str(row.time) + '","' + str(row.id) + '",'
#                if params['questionTitle'] == 'true':
#                    csv = csv + '"' + row.title + '",'
#                if params['questionBody'] == 'true':
#                    csv = csv + '"' + row.content + '",'
#                csv = csv[:-1] + '\n'
#
#                if params['questionComments'] == 'true':
#                    query = CommentQ.query.filter_by(qid = row.id)
#                    if "startdate" in params:
#                        query = query.filter(cast(Entry.time, DATE) >= startdate)
#                    if "enddate" in params:
#                        query = query.filter(cast(Entry.time, DATE) <= enddate)
#                    commentsQ = query.all()
#                    for c_row in commentsQ:
#                        comments = comments + '"' + c_row.content + '"\n'
#            if params['questionComments'] == 'true':
#                comments = '\n"Question Comments"\n' + comments
#                csv = csv + comments
#                comments = ''
#
#        if params['answer'] == 'true':
#            header = '"author","time","scores","question #"'
#            if params['answerBody'] == 'true':
#                header = header + ',"answer"'
#            query = Script.query.filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid)))
#            if "startdate" in params:
#                query = query.filter(cast(Entry.time, DATE) >= startdate)
#            if "enddate" in params:
#                query = query.filter(cast(Entry.time, DATE) <= enddate)
#            answers = query.all()
#            csv = csv + '\n"Answers"\n' + header + '\n'
#            for row in answers:
#                author = User.query.filter_by(id = row.uid).first()
#                scoreString = ''
#                categories = JudgementCategory.query.filter_by(cid = cid).all()
#                for crit in categories:
#                    score = ScriptScore.query.filter_by(sid = row.id).filter_by(jcid = crit.id).first()
#                    if score:
#                        scoreString = scoreString + crit.name + ': ' + str(score.score) + ';'
#                    else:
#                        scoreString = scoreString + crit.name + ': ' + str(0) + ';'
#                csv = csv + '"' + author.display + '","' + str(row.time) + '","' + scoreString[:-1] + '","' + str(row.qid) + '",'
#                if params['answerBody'] == 'true':
#                    csv = csv + '"' + row.content + '",'
#                csv = csv[:-1] + '\n'
#
#                if params['answerComments'] == 'true':
#                    query = CommentA.query.filter_by(sid = row.id)
#                    if "startdate" in params:
#                        query = query.filter(cast(Entry.time, DATE) >= startdate)
#                    if "enddate" in params:
#                        query = query.filter(cast(Entry.time, DATE) <= enddate)
#                    commentsA = query.all()
#                    for c_row in commentsA:
#                        comments = comments + '"' + c_row.content + '"\n'
#            if params['answerComments'] == 'true':
#                comments = '\n"Answer Comments"\n' + comments
#                csv = csv + comments
#                comments = ''
#        if params['judgement'] == 'true':
#            header = '"judge","author answer 1","author answer 2"'
#            if params['judgementQuestion'] == 'true':
#                header = header + ',"title","question"'
#            if params['judgementAnswer'] == 'true':
#                header = header + ',"answer 1","answer 2"'
#            header = header + ',"winner"'
#            questionsJ = Question.query.with_entities(Question.id).filter_by(cid = cid)
#            csv = csv + '\n"Judgements"\n' + header + '\n'
#            for question in questionsJ:
#                query = Judgement.query.filter(Judgement.script1.has(qid = question.id))
#                if "startdate" in params:
#                    query = query.filter(cast(Judgement.time, DATE) >= startdate)
#                if "enddate" in params:
#                    query = query.filter(cast(Judgement.time, DATE) <= enddate)
#                judgements = query.all()
#                for row in judgements:
#                    judge = User.query.filter_by(id = row.uid).first()
#                    author1 = User.query.filter_by(id = row.script1.uid).first()
#                    author2 = User.query.filter_by(id = row.script2.uid).first()
#
#                    csv = csv + '"' + judge.display + '","' + author1.display + '","' + author2.display + '",'
#                    if params['judgementQuestion'] == 'true':
#                        questionsJ = Question.query.filter_by(id = row.script1.qid).all()
#                        for rowQ in questionsJ:
#                                csv = csv + '"' + rowQ.title + '",' + '"' + rowQ.content + '",'
#                    if params['judgementAnswer'] == 'true':
#                        csv = csv + '"' + row.script1.content + '","' + row.script2.content + '",'
#
#                    winnerString = ''
#                    categories = JudgementCategory.query.filter_by(cid = cid).all()
#                    for crit in categories:
#                        winner = JudgementWinner.query.filter_by(jid = row.id).filter_by(jcid = crit.id).all()
#                        if winner == row.sidl:
#                            winnerString = winnerString + crit.name + ': ' + author1.display + ';'
#                        else:
#                            winnerString = winnerString + crit.name + ': ' + author2.display + ';'
#                    csv = csv + '"' + winnerString[:-1] + '"\n'
#                    if params['judgementComments'] == 'true':
#                        commentsJ = CommentJ.query.filter_by(sidl = row.script1.id).filter_by(sidr = row.script2.id).all()
#                        for c_row in commentsJ:
#                            comments = comments + c_row.content + '\n'
#            if params['judgementComments'] == 'true':
#                comments = '\n"Judgement Comments"\n' + comments
#                csv = csv + comments
#                comments = ''
#    else :
#        if params['userdata'] == 'true':
#            header = '"user", "first name","last name","# questions authored", "# questions answered", "avg score / answer", "# pairs ranked"'
#            query = User.query.filter(User.id.in_(Enrollment.query.with_entities(Enrollment.uid).filter_by(cid = cid)))
#            if "startdate" in params:
#                query = query.filter(cast(Entry.time, DATE) >= startdate)
#            if "enddate" in params:
#                query = query.filter(cast(Entry.time, DATE) <= enddate)
#            users = query.all()
#            csv = csv + '\n"User"\n' + header + '\n'
#
#            query = Question.query.filter_by(cid = cid)
#            if "startdate" in params:
#                query = query.filter(cast(Entry.time, DATE) >= startdate)
#            if "enddate" in params:
#                query = query.filter(cast(Entry.time, DATE) <= enddate)
#            totalQuestionCount = query.count()
#
#            query = Script.query.filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid)))
#            if "startdate" in params:
#                query = query.filter(cast(Entry.time, DATE) >= startdate)
#            if "enddate" in params:
#                query = query.filter(cast(Entry.time, DATE) <= enddate)
#            totalAnswerCount = query.count()
#
#            for row in users:
#                query = Question.query.filter_by(uid = row.id).filter_by(cid = cid)
#                if "startdate" in params:
#                    query = query.filter(cast(Entry.time, DATE) >= startdate)
#                if "enddate" in params:
#                    query = query.filter(cast(Entry.time, DATE) <= enddate)
#                qCount = query.count()
#                query = Script.query.filter_by(uid = row.id).filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid)))
#                if "startdate" in params:
#                    query = query.filter(cast(Entry.time, DATE) >= startdate)
#                if "enddate" in params:
#                    query = query.filter(cast(Entry.time, DATE) <= enddate)
#                aCount = query.count()
#                if "startdate" in params and "enddate" in params:
#                    query = ScriptScore.query.with_entities(func.avg(ScriptScore.score).label('average')).filter(ScriptScore.sid.in_(Script.query.with_entities(Script.id).filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).filter(cast(Entry.time, DATE) >= startdate).filter(cast(Entry.time, DATE) <= enddate).filter_by(uid = row.id)))
#                elif "startdate" in params:
#                    query = ScriptScore.query.with_entities(func.avg(ScriptScore.score).label('average')).filter(ScriptScore.sid.in_(Script.query.with_entities(Script.id).filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).filter(cast(Entry.time, DATE) >= startdate).filter_by(uid = row.id)))
#                elif "enddate" in params:
#                    query = ScriptScore.query.with_entities(func.avg(ScriptScore.score).label('average')).filter(ScriptScore.sid.in_(Script.query.with_entities(Script.id).filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).filter(cast(Entry.time, DATE) <= enddate).filter_by(uid = row.id)))
#                else:
#                    query = ScriptScore.query.with_entities(func.avg(ScriptScore.score).label('average')).filter(ScriptScore.sid.in_(Script.query.with_entities(Script.id).filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid))).filter_by(uid = row.id)))
#                answerAvg = query.first()
#                if (answerAvg[0]):
#                    avg = format(Decimal(answerAvg[0]), '.2f')
#                else:
#                    avg = '-'
#                query = Judgement.query.filter_by(uid = row.id).filter(Judgement.sidl.in_(Script.query.with_entities(Script.id).filter(Script.qid.in_(Question.query.with_entities(Question.id).filter_by(cid = cid)))))
#                if "startdate" in params:
#                    query = query.filter(cast(Judgement.time, DATE) >= startdate)
#                if "enddate" in params:
#                    query = query.filter(cast(Judgement.time, DATE) <= enddate)
#                pairCount = query.count()
#                csv = csv + '"' + row.display + '","' + row.firstname + '","' + row.lastname + '","' + str(qCount) + '","' + str(aCount) + '","' + avg + '","' + str(pairCount) + '"\n'
#    return Response(csv, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=statistics.csv"})
#
#@app.route('/enrollment/<id>', methods=['GET', 'PUT', 'POST', 'DELETE'])
#@student.require(http_exception=401)
#def manage_enrollment(id):
#    if "Admin" in session["identity.id"] or "Teacher" in session["identity.id"]:
#        if request.method == "GET":
#            return students_enrolled(id)
#        elif request.method == "POST":
#            return enroll_student(id)
#        elif request.method == "PUT":
#            return change_role(id)
#        elif request.method == "DELETE":
#            return drop_student(id)
#    else:
#        if request.method == "DELETE":
#            role = Enrollment.query.filter_by(id = id).first().userrole.role
#        else:
#            userId = User.query.filter_by(username = session['username']).first().id
#            role = Enrollment.query.filter_by(cid = id).filter_by(uid = userId).first().userrole.role
#        if role == 'Teacher':
#            oldIdentity = session["identity.id"]
#            newIdentity = Identity('only_' + role)
#            identity_changed.send(app, identity=newIdentity)
#            if request.method == "GET":
#                response = students_enrolled(id)
#            elif request.method == "POST":
#                response = enroll_student(id)
#            elif request.method == "PUT":
#                response = change_role(id)
#            elif request.method == "DELETE":
#                response = drop_student(id)
#            identity_changed.send(app, identity=Identity(oldIdentity))
#            return response
#        elif request.method == "GET":
#            return students_enrolled(id)
#        elif request.method == "POST":
#            return enroll_student(id)
#        elif request.method == "PUT":
#            return change_role(id)
#        elif request.method == "DELETE":
#            return drop_student(id)
#
#@teacher.require(http_exception=401)
#def students_enrolled(cid):
#    #this is called as a AJAX request to only return a limited set of students or teachers
#    start = int(request.args['start'])
#    end = int(request.args['end'])
#    if request.args['type'] == 'Teacher':
#        users = User.query.join(UserRole).filter((User.userrole.has(UserRole.role == 'Teacher')))
#    else:
#        users = User.query.join(UserRole).filter((User.userrole.has(UserRole.role == 'Student')))
#    #filter the dataset
#    if "filter" in request.args:
#        users = users.filter(func.lower(User.fullname).like('%' + request.args['filter'] + '%'))
#    #sort the dataset
#    if "sorting" in request.args:
#        #sort by name
#        if request.args['sortingtype'] == "username":
#            if request.args['sorting'] == "desc":
#                users = users.order_by( User.fullname.desc() )
#            else:
#                users = users.order_by( User.fullname )
#        #sort by 'enrolled' attribute
#        elif request.args['sortingtype'] == "enrolled":
#            enroll = Enrollment.query.filter_by(uid = User.id).filter_by(cid = cid).exists()
#            if request.args['sorting'] == "desc":
#                users = users.order_by( enroll.desc() )
#            else:
#                users = users.order_by( enroll )
#    #get the total number of teachers / students
#    usercount = users.count()
#    #but only process a limited set
#    users = users.slice(start,end)
#    studentlst = []
#    teacherlst = []
#    for user in users:
#        enrolled = ''
#        query = Enrollment.query.filter_by(uid = user.id).filter_by(cid = cid).first()
#        userrole = user.userrole.role
#        if (query):
#            enrolled = query.id
#            userrole = UserRole.query.filter_by(id = query.usertype).first().role
#        if user.userrole.role == 'Student':
#            studentlst.append( {"uid": user.id, "username": user.fullname, "enrolled": enrolled, "role": userrole} )
#        else:
#            teacherlst.append( {"uid": user.id, "username": user.fullname, "enrolled": enrolled, "role": userrole} )
#    course = Course.query.filter_by(id = cid).first()
#    retval = json.dumps( { "course": course.name, "students": studentlst, "teachers": teacherlst, "count": usercount} )
#    db.session.rollback()
#    return retval
#
#@teacher.require(http_exception=401)
#def enroll_student(cid):
#    user = {'user': {'id': request.json['uid']}}
#    retval = enrol_users([user], cid)
#    return json.dumps(retval)
#
#@teacher.require(http_exception=401)
#def change_role(cid):
#    uid = request.json['uid']
#    role = request.json['role']
#    enrol = Enrollment.query.filter_by(uid = uid).filter_by(cid = cid).first()
#    userrole = UserRole.query.filter_by(role = role).first()
#    enrol.usertype = userrole.id
#    commit()
#    return json.dumps({"msg": "PASS", "role": userrole.role})
#
#@teacher.require(http_exception=401)
#def drop_student(eid):
#    query = Enrollment.query.filter_by( id = eid ).first()
#    db.session.delete(query)
#    commit()
#    return json.dumps( {"msg": "PASS"} )
#
#@app.route('/rolecheck/<cid>/<qid>')
#@student.require(http_exception=401)
#def check_role(cid, qid):
#    if cid == "-1":
#        cid = Question.query.filter_by(id = qid).first().cid
#    userId = User.query.filter_by(username = session['username']).first().id
#    role = Enrollment.query.filter_by(cid = cid).filter_by(uid = userId).first().userrole.role
#    return json.dumps({"msg": "PASS", "role": role})
