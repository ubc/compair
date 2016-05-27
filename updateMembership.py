from acj.sqlalchemy_acj import db_session, LTIInfo, Course, User, Enrollment
from acj.general import commit
from werkzeug import urls
import oauth.oauth as oauth
import hmac
import base64
import hashlib
import requests
import xml.etree.ElementTree as ET
from acj.users import import_users
from acj.course import enrol_users
#get all courses to update
courses = LTIInfo.query.all()
for course in courses:
    #iterate through courses and get their membership info via LTI
    timestamp = oauth.generate_timestamp()
    nonce = oauth.generate_nonce(16)
    postParams = {}
    postParams['lti_message_type'] = 'basic-lis-readmembershipsforcontext'
    postParams['id'] = course.LTIid
    postParams['lti_version'] = 'LTI-1p0'
    postParams['oauth_consumer_key'] = 'LTI_ACJ'
    postParams['oauth_callback'] = 'about:blank'
    postParams['oauth_version'] = '1.0'
    postParams['oauth_signature_method'] = 'HMAC-SHA1'
    postParams['oauth_timestamp'] = timestamp
    postParams['oauth_nonce'] = nonce

    req = oauth.OAuthRequest(http_url=course.LTIURL, http_method='POST', parameters=postParams)
    hmacAlg = hmac.HMAC('acjsecret&', urls.url_quote_plus(req.get_normalized_http_method()) + '&' + urls.url_quote_plus(course.LTIURL) + '&' + urls.url_quote_plus(req.get_normalized_parameters()), hashlib.sha1)

    postParams['oauth_signature'] = base64.b64encode(hmacAlg.digest())

    xmlString = requests.post(course.LTIURL, data=postParams).text
    root = ET.fromstring(xmlString)
    #find the course in ACJ, create if it does not exist
    tmpCourse = Course.query.filter_by(name = course.courseName).first()
    if not tmpCourse:
        newCourse = Course(course.courseName)
        db_session.add(newCourse)
        commit()

    #create a list with all users in the course
    userlist = []
    for member in root.find('memberships').findall('member'):
        role = 'Student'
        if member.find('roles').text and 'Instructor' in member.find('roles').text:
            role = 'Teacher'
        userlist.append({"username": member.find('person_sourcedid').text, "password": member.find('person_sourcedid').text,
                         "usertype": role, "email": member.find('person_contact_email_primary').text, "firstname": member.find('person_name_given').text,
                         "lastname": member.find('person_name_family').text, "display": member.find('person_name_full').text})
    #add missing users to ACJ
    if userlist:
        import_users(userlist)
    #enroll users to the course
    courseId = Course.query.filter_by(name = course.courseName).first().id
    for member in root.find('memberships').findall('member'):
        userId = User.query.filter_by(username = member.find('person_sourcedid').text).first().id

        enrolled = Enrollment.query.filter_by(cid = courseId).with_entities(Enrollment.uid).all()
        enrolled =  [item for sublist in enrolled for item in sublist]
        if userId not in enrolled:
            usertype = User.query.filter_by(id = userId).first().userrole.id
            table = Enrollment(userId, courseId, usertype)
            db_session.add(table)
            commit()