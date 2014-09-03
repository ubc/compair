import datetime
from acj import db
from acj.manage.database import populate
from acj.models import UserTypesForSystem, UserTypesForCourse, Users, CoursesAndUsers, Courses
from data.fixtures import SampleDataFixture
from tests.factories import CoursesFactory, PostsFactory, PostsForAnswersFactory, PostsForQuestionsFactory, \
	UsersFactory, CoursesAndUsersFactory, PostsForCommentsFactory, PostsForQuestionsAndPostsForCommentsFactory, \
	PostsForAnswersAndPostsForCommentsFactory


class SimpleTestData():
	def __init__(self):
		self.course = CoursesFactory()
		db.session.commit()
		# create 2 instructors and 2 students, 1 of each will be enroled in the course
		self.unenroled_instructor = self.create_user(UserTypesForSystem.TYPE_INSTRUCTOR)
		self.unenroled_student = self.create_user(UserTypesForSystem.TYPE_NORMAL)
		self.enroled_instructor = self.create_user(UserTypesForSystem.TYPE_INSTRUCTOR)
		self.enrol_user(self.enroled_instructor, self.course, UserTypesForCourse.TYPE_INSTRUCTOR)
		self.enroled_student = self.create_user(UserTypesForSystem.TYPE_NORMAL)
		self.enrol_user(self.enroled_student, self.course, UserTypesForCourse.TYPE_STUDENT)
		# add 2 questions, each with 2 answers, to the course
		self.questions = []
		self.answers = []
		answer_start = datetime.datetime.now() - datetime.timedelta(days=2)
		answer_end = datetime.datetime.now() - datetime.timedelta(days=1)
		question = self.create_question(self.course, self.enroled_instructor, answer_start, answer_end)
		self.questions.append(question)
		answer = self.create_answer(question, self.enroled_student)
		self.answers.append(answer)

		self.post_answer_comment(self.enroled_student, self.course, question, answer)
		answer = self.create_answer(question, self.enroled_student)
		self.answers.append(answer)
		self.post_question_comment(self.enroled_student, self.course, question)
		answer_start = datetime.datetime.now()
		answer_end = datetime.datetime.now() +  datetime.timedelta(days=7)
		question = self.create_question(self.course, self.enroled_instructor, answer_start, answer_end)
		self.questions.append(question)
		answer = self.create_answer(question, self.enroled_student)
		self.answers.append(answer)
		answer = self.create_answer(question, self.enroled_student)
		self.answers.append(answer)

	def create_answer(self, question, author):
		post = PostsFactory(courses_id = question.post.courses_id, users_id = author.id)
		db.session.commit()
		answer = PostsForAnswersFactory(postsforquestions_id=question.id, posts_id = post.id)
		db.session.commit()
		return answer

	def create_question(self, course, author, answer_start, answer_end):
		post = PostsFactory(courses_id = course.id, users_id = author.id)
		db.session.commit()
		question = PostsForQuestionsFactory(posts_id = post.id, answer_start = answer_start, answer_end = answer_end)
		db.session.commit()
		return question

	def create_user(self, type):
		sys_type = UserTypesForSystem.query.filter_by(name=type). \
			first()
		user = UsersFactory(usertypesforsystem_id=sys_type.id)
		db.session.commit()
		return user

	def enrol_user(self, user, course, type):
		course_type = UserTypesForCourse.query. \
			filter_by(name=type).first()
		CoursesAndUsersFactory(courses_id=course.id, users_id=user.id,
							   usertypesforcourse_id=course_type.id)
		db.session.commit()

	def post_question_comment(self, author, course, question):
		post = PostsFactory(courses_id = course.id, users_id = author.id)
		db.session.commit()
		comment = PostsForCommentsFactory(posts_id = post.id)
		db.session.commit()
		quesComment = PostsForQuestionsAndPostsForCommentsFactory(postsforcomments_id = comment.id, postsforquestions_id = question.id)
		db.session.commit()

	def post_answer_comment(self, author, course, question, answer):
		post = PostsFactory(courses_id = course.id, users_id = author.id)
		db.session.commit()
		comment = PostsForCommentsFactory(posts_id = post.id)
		db.session.commit()
		answerComment = PostsForAnswersAndPostsForCommentsFactory(postsforcomments_id = comment.id, postsforanswers_id = answer.id)
		db.session.commit()

	def get_course(self):
		return self.course
	def get_enroled_instructor(self):
		return self.enroled_instructor
	def get_unenroled_instructor(self):
		return self.unenroled_instructor
	def get_enroled_student(self):
		return self.enroled_student
	def get_unenroled_student(self):
		return self.unenroled_student
	def get_questions(self):
		return self.questions
	def get_answers(self):
		return self.answers

class GeneratedTestData():
	'''
	Uses the sample data fixture to populate the database.
	'''
	def __init__(self):
		populate(default_data=False, sample_data=True)

	def get_user_enroled_courses(self, user):
		course_enrolments = CoursesAndUsers.query.filter(user=user).all()
		return [course_enrolment.course for course_enrolment in course_enrolments]

	def get_courses(self):
		return Courses.query.filter(Courses.name.in_(SampleDataFixture.COURSE_NAMES)).all()

	def get_instructors(self):
		return Users.query.filter(Users.username.in_(SampleDataFixture.INSTRUCTOR_NAMES)).all()

	def get_students(self):
		return Users.query.filter(Users.username.in_(SampleDataFixture.STUDENT_NAMES)).all()



