from __future__ import division
from flask import Flask, url_for, request, render_template, redirect, escape, session
from sqlalchemy_acj import db, User, Judgement, Script
from sqlalchemy import desc
import exceptions
import MySQLdb
import re
import phpass
import json

app = Flask(__name__)

db.create_all()

hash = phpass.PasswordHash()

@app.route('/')
def index():
	return redirect(url_for('static', filename="index.html"))

@app.route('/script/<id>', methods=['GET'])
def get_script(id):
	print(id)
	query = Script.query.filter_by(id = id).first()
	if not query:
		return json.dumps({"msg": "No matching script"})
	ret_val = json.dumps( {"content": query.content} )
	return ret_val

@app.route('/script/<id>', methods=['POST'])
def mark_script(id):
	query = Script.query.filter_by(id = id).first()
	if not query:
		return json.dumps({"msg": "No matching script"})
	query.score = query.score + 1
	db.session.commit()
	print (query.score)
	return json.dumps({"msg": "Script score updated"})








app.secret_key = 'asdf1234'

if __name__=='__main__':
	app.run(debug=True)
