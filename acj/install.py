from sqlalchemy_acj import db_session, init_db, UserRole

init_db()

print "Installing..."
try:
	print "Initializing Database"
	UserRole.query.delete() # drop all prior roles, if any
	# (re)create the roles
	role = UserRole(UserRole.ADMIN_ROLE)
	db_session.add(role)
	role = UserRole(UserRole.STUDENT_ROLE)
	db_session.add(role)
	role = UserRole(UserRole.INSTRUCTOR_ROLE)
	db_session.add(role)
	db_session.commit()
except:
	print "Installation Failed"
	raise

