from acj import app
from sqlalchemy_acj import db_session, User, Course
from flask import request, session, redirect, url_for
from werkzeug import urls
from flask_principal import AnonymousIdentity, Identity, identity_changed
from general import commit
import oauth.oauth as oauth
import hmac
import base64
import hashlib
import requests
import xml.etree.ElementTree as ET
from users import import_users
from course import enrol_users

def updateMembership(url, id, params):
    postParams = {}
    postParams['lti_message_type'] = 'basic-lis-readmembershipsforcontext'
    postParams['id'] = id
    postParams['lti_version'] = 'LTI-1p0'
    postParams['oauth_consumer_key'] = params['oauth_consumer_key']
    postParams['oauth_callback'] = params['oauth_callback']
    postParams['oauth_version'] = params['oauth_version']
    postParams['oauth_signature_method'] = params['oauth_signature_method']
    postParams['oauth_timestamp'] = params['oauth_timestamp']
    postParams['oauth_nonce'] = params['oauth_nonce']
    
    req = oauth.OAuthRequest(http_url=url, http_method='POST', parameters=postParams)
    hmacAlg = hmac.HMAC('acjsecret&', urls.url_quote_plus(req.get_normalized_http_method()) + '&' + urls.url_quote_plus(url) + '&' + urls.url_quote_plus(req.get_normalized_parameters()), hashlib.sha1)
    
    postParams['oauth_signature'] = base64.b64encode(hmacAlg.digest())
    
    xmlString = requests.post(url, data=postParams).text
    root = ET.fromstring(xmlString)
    
     #find the course, create it if not exists
    course = Course.query.filter_by(name = params['context_title']).first()
    if not course:
        name = params['context_title']
        newCourse = Course(name)
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
    course = Course.query.filter_by(name = params['context_title']).first()
    for member in root.find('memberships').findall('member'):
        userId = User.query.filter_by(username = member.find('person_sourcedid').text).first().id
        ret = enrol_users( [{'user': {'id': userId}}], course.id)
    
@app.route('/', methods=['POST'])
def sso():
    params = request.form.copy()
    if params['oauth_consumer_key'] and params['oauth_consumer_key'] == 'LTI_ACJ':
        req = oauth.OAuthRequest(http_url='/', http_method='POST', parameters=params)
        hmacAlg = hmac.HMAC('acjsecret&', urls.url_quote_plus(req.get_normalized_http_method()) + '&' + urls.url_quote_plus(request.url) + '&' + urls.url_quote_plus(req.get_normalized_parameters()), hashlib.sha1)
        if request.form['oauth_signature'] == base64.b64encode(hmacAlg.digest()):
            #log user in
            session['username'] = params['lis_person_sourcedid']
            query = User.query.filter_by(username = session['username']).first()
            if not query:
                session.pop('username', None)
                for key in ['identity.name', 'identity.auth_type']:
                    session.pop(key, None)
                identity_changed.send(app, identity=AnonymousIdentity())
                return redirect(url_for('static', filename="index.html"))
        
            usertype = query.usertype
            display = query.display
            db_session.rollback()
            identity = Identity('only_' + query.usertype)
            identity_changed.send(app, identity=identity)
            if query.usertype != "Student":
                updateMembership(params['ext_ims_lis_memberships_url'], params['ext_ims_lis_memberships_id'], params)
            return redirect(url_for('static', filename="index.html"))
        else:
            session.pop('username', None)
            for key in ['identity.name', 'identity.auth_type']:
                session.pop(key, None)
            identity_changed.send(app, identity=AnonymousIdentity())
            return redirect(url_for('static', filename="index.html"))