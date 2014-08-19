import datetime
from acj import db
from acj.models import UserTypesForSystem, UserTypesForCourse
from data.fixtures import CoursesFactory, UsersFactory, CoursesAndUsersFactory, PostsFactory, PostsForQuestionsFactory, \
	PostsForAnswersFactory


class BasicTestData():
	def __init__(self):
		self.main_course = self.create_course()
		self.secondary_course = self.create_course()
		self.authorized_instructor = self.create_instructor()
		self.authorized_student = self.create_student()
		self.unauthorized_instructor = self.create_instructor() # unauthorized to the main course
		self.unauthorized_student = self.create_student()
		self.enrol_instructor(self.authorized_instructor, self.main_course)
		self.enrol_student(self.authorized_student, self.main_course)
		self.enrol_instructor(self.unauthorized_instructor, self.secondary_course)
		self.enrol_student(self.unauthorized_student, self.secondary_course)
	def create_course(self):
		course = CoursesFactory()
		db.session.commit()
		return course
	def create_instructor(self):
		return self.create_user(UserTypesForSystem.TYPE_INSTRUCTOR)
	def create_student(self):
		return self.create_user(UserTypesForSystem.TYPE_NORMAL)
	def create_user(self, type):
		sys_type = UserTypesForSystem.query.filter_by(name=type).first()
		user = UsersFactory(usertypesforsystem_id=sys_type.id)
		db.session.commit()
		return user
	def enrol_student(self, user, course):
		self.enrol_user(user, course, UserTypesForCourse.TYPE_STUDENT)
	def enrol_instructor(self, user, course):
		self.enrol_user(user, course, UserTypesForCourse.TYPE_INSTRUCTOR)
	def enrol_user(self, user, course, type):
		course_type = UserTypesForCourse.query.filter_by(name=type).first()
		CoursesAndUsersFactory(courses_id=course.id, users_id=user.id,
							   usertypesforcourse_id=course_type.id)
		db.session.commit()
	def get_authorized_instructor(self):
		return self.authorized_instructor
	def get_authorized_student(self):
		return self.authorized_student
	def get_course(self):
		return self.main_course
	def get_unauthorized_instructor(self):
		return self.unauthorized_instructor
	def get_unauthorized_student(self):
		return self.unauthorized_student

class SimpleQuestionsTestData(BasicTestData):
	def __init__(self):
		BasicTestData.__init__(self)
		self.questions = []
		self.questions.append(self.create_question_in_answer_period(self.get_course(),\
			self.get_authorized_instructor()))
		self.questions.append(self.create_question_in_answer_period(self.get_course(), \
			self.get_authorized_instructor()))

	def create_question_in_judgement_period(self, course, author):
		answer_start = datetime.datetime.now() - datetime.timedelta(days=2)
		answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
		return self.create_question(course, author, answer_start, answer_end)

	def create_question_in_answer_period(self, course, author):
		answer_start = datetime.datetime.now() - datetime.timedelta(days=1)
		answer_end = datetime.datetime.now() + datetime.timedelta(days=1)
		return self.create_question(course, author, answer_start, answer_end)

	def create_question(self, course, author, answer_start, answer_end):
		post = PostsFactory(courses_id = course.id, users_id = author.id)
		db.session.commit()
		question = PostsForQuestionsFactory(posts_id = post.id, answer_start = answer_start, answer_end = answer_end)
		db.session.commit()
		return question

	def get_questions(self):
		return self.questions

class SimpleAnswersTestData(SimpleQuestionsTestData):
	def __init__(self):
		SimpleQuestionsTestData.__init__(self)
		extra_student1 = self.create_student()
		extra_student2 = self.create_student()
		self.enrol_student(extra_student1, self.get_course())
		self.enrol_student(extra_student2, self.get_course())
		self.answers = []
		for question in self.get_questions():
			self.answers.append(self.create_answer(question, extra_student1))
			self.answers.append(self.create_answer(question, extra_student2))

	def create_answer(self, question, author):
		post = PostsFactory(courses_id = question.post.courses_id, users_id = author.id)
		db.session.commit()
		answer = PostsForAnswersFactory(postsforquestions_id=question.id, posts_id = post.id)
		db.session.commit()
		return answer

	def get_answers(self):
		return self.answers

class JudgmentsTestData(SimpleAnswersTestData):
	def __init__(self):
		SimpleAnswersTestData.__init__(self)
		for question in self.get_questions():
			self.set_question_to_judgement_period(question)

	def set_question_to_judgement_period(self, question):
		question.answer_start = datetime.datetime.now() - datetime.timedelta(days=2)
		question.answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
		db.session.add(question)
		db.session.commit()
		return question

