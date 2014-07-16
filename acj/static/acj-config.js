var myApp = angular.module('myApp', [
	'ngRoute', 
	'ngResource',
	'ngTable', 
	'http-auth-interceptor', 
	'ngCookies', 
	'ngUpload',
	'ng-breadcrumbs',
	'angular-loading-bar',
	'ubc.ctlt.acj.common.flash', // TODO Remove once split into modules done
	'ubc.ctlt.acj.common.installed', // TODO Remove once split into modules done
	'ubc.ctlt.acj.answer',
	'ubc.ctlt.acj.course',
	'ubc.ctlt.acj.home',
	'ubc.ctlt.acj.installer',
	'ubc.ctlt.acj.login',
	'ubc.ctlt.acj.navbar',
	'ubc.ctlt.acj.question'
]);

//Global Variables

myApp.factory('judgeService', function($resource) {
	return $resource( '/script/:scriptId' );
});

// TODO REMOVE LOGINSERVICE AND LOGOUTSERVICE LATER ONCE ALL REFERENCES HAVE BEEN REMOVED
myApp.factory('loginService', function($resource) {
	return $resource( '/login' );
});
myApp.factory('logoutService', function($resource) {
	return $resource( '/logout' );
});

myApp.factory('roleService', function($resource) {
	return $resource( '/roles' );
});

myApp.factory('userService', function($resource) {
	return $resource( '/user/:uid', {}, { put: {method: 'PUT'} } );
});

myApp.factory('allUserService', function($resource) {
	return $resource( '/allUsers' );
});

myApp.factory('pickscriptService', function($resource) {
	return $resource( '/pickscript/:qid/:sidl/:sidr', {sidl: 0, sidr: 0} );
});

myApp.factory('rankService', function($resource) {
	return $resource( '/ranking/:qid' );
});

myApp.factory('courseService', function($resource) {
	return $resource( '/course' );
});

myApp.factory('editcourseService', function($resource) {
	return $resource( '/editcourse/:cid', {}, { put: {method: 'PUT'} } );
});

myApp.factory('questionService', function($resource) {
	return $resource( '/question/:cid', {}, { put: {method: 'PUT'} } );
});

myApp.factory('answerService', function($resource) {
	return $resource( '/answer/:qid', {}, { put: {method: 'PUT'} } );
});

myApp.factory('quickService', function($resource) {
	return $resource( '/randquestion' );
});

myApp.factory('enrollService', function($resource) {
	return $resource( '/enrollment/:id', {}, { put: {method: 'PUT'} } );
});

myApp.factory('commentAService', function($resource) {
	return $resource( '/answer/:id/comment', {}, { put: {method: 'PUT'} } );
});

myApp.factory('commentQService', function($resource) {
	return $resource( '/question/:id/comment', {}, { put: {method: 'PUT'} } );
});

myApp.factory('commentJService', function($resource) {
	return $resource( '/judgepage/:id/comment/:sidl/:sidr', {}, { put: {method: 'PUT'} } );
});

myApp.factory('passwordService', function($resource) {
	return $resource( '/password/:uid' );
});

myApp.factory('reviewjudgeService', function($resource) {
	return $resource( '/judgements/:qid' );
});

myApp.factory('notificationService', function($resource) {
	return $resource( '/notifications' );
});

myApp.factory('critService', function($resource) {
	return $resource( '/managecategories/:cid/:critid' );
});

myApp.factory('tagService', function($resource) {
	return $resource( '/managetag/:cid/:tid' );
});

myApp.factory('statisticService', function($resource) {
	return $resource( '/statistics/:cid' );
});

myApp.factory('statisticExportService', function($resource) {
	return $resource( '/statisticexport/', {}, { put: {method: 'POST'} } );
});

myApp.factory('rolecheckService', function($resource) {
	return $resource( '/rolecheck/:cid/:qid' );
});

//used for testing
myApp.factory('resetDB', function($resource) {
	return $resource( '/resetdb' );
});

myApp.config( function ($routeProvider) {
	$routeProvider
		.when ('/', 
			{
				templateUrl: 'modules/home/home-partial.html',
				label: "Home" // breadcrumb label
			})
		.when ('/course/new', 
			{
				templateUrl: 'modules/course/course-create-partial.html',
				label: "Create New Course"
			})
		.when ('/course/:courseId', 
			{
				templateUrl: 'modules/course/course-questions-partial.html',
				label: "Course Questions"
			})
		.when ('/course/:courseId/configure', 
			{
				templateUrl: 'modules/course/course-configure-partial.html',
				label: "Course Configuration"
			})
		.when ('/course/:courseId/question/create', 
			{
				templateUrl: 'modules/question/question-create-partial.html',
				label: "Create Question"
			})
		.when ('/course/:courseId/question/:questionId', 
			{
				templateUrl: 'modules/question/question-view-partial.html',
				label: "View Question"
			})
		.when ('/course/:courseId/question/:questionId/edit',
			{
				templateUrl: 'modules/question/question-edit-partial.html',
				label: "Question Configuration"
			})
		.when ('/course/:courseId/question/:questionId/answer/create', 
			{
				templateUrl: 'modules/answer/answer-create-partial.html',
				label: "Post Answer"
			})
		.when ('/install', 
			{
				templateUrl: 'modules/installer/installer-partial.html',
				label: "Installer Step 1"
			})
		.when ('/install2', 
			{
				templateUrl: 'install2.html',
				label: "Installer Step 2"
			})
		.when ('/judgepage/:questionId',
			{
				controller: JudgepageController,
				templateUrl: 'judgepage.html'
			})
		.when ('/createuser',
			{
				controller: UserController,
				templateUrl: 'createuser.html'
			})
		.when ('/user',
			{
				controller: UserIndexController,
				templateUrl: 'userpage.html'
			})
//		.when ('/rankpage',
//			{
//				controller: RankController,
//				templateUrl: 'rankpage.html'
//			})
		.when ('/questionpage/:courseId',
			{
				controller: QuestionController,
				templateUrl: 'questionpage.html'
			})
		.when ('/answerpage/:questionId',
			{
				controller: AnswerController,
				templateUrl: 'answerpage.html'
			})
		.when ('/enrollpage/:courseId',
			{
				controller: EnrollController,
				templateUrl: 'enrollpage.html'
			})
		.when ('/quickjudge',
			{
				controller: QuickController,
				templateUrl: 'judgepage.html'
			})
		.when ('/userprofile/:userId',
			{
				controller: ProfileController,
				templateUrl: 'userprofile.html'
			})
		.when('/classimport',
			{
				controller: ImportController,
				templateUrl: 'classimport.html'
			})
		.when ('/reviewjudge/:qid',
			{
				controller: ReviewJudgeController,
				templateUrl: 'reviewjudge.html'
			})
		.when ('/stats/:courseId',
			{
				controller: StatisticController,
				templateUrl: 'stats.html'
			})
		.when ('/statexport/:cid/:cname',
				{
			controller: StatisticExportController,
			templateUrl: 'statexport.html'
			})
		.otherwise({redirectTo: '/'});
});
