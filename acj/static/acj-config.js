var myApp = angular.module('myApp', [
	'ngRoute', 
	'http-auth-interceptor', 
	'ngCookies', 
	'ng-breadcrumbs',
	'angular-loading-bar',
	'ubc.ctlt.acj.answer',
	'ubc.ctlt.acj.attachment',
	'ubc.ctlt.acj.classlist',
	'ubc.ctlt.acj.comment',
	'ubc.ctlt.acj.course',
	'ubc.ctlt.acj.criteria',
	'ubc.ctlt.acj.group',
	'ubc.ctlt.acj.gradebook',
	'ubc.ctlt.acj.home',
	'ubc.ctlt.acj.judgement',
	'ubc.ctlt.acj.login',
	'ubc.ctlt.acj.navbar',
	'ubc.ctlt.acj.question',
	'ubc.ctlt.acj.report'
]);

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
				label: "Add Course"
			})
		.when ('/course/:courseId', 
			{
				templateUrl: 'modules/course/course-questions-partial.html',
				label: "Course Questions"
			})
		.when ('/course/:courseId/configure', 
			{
				templateUrl: 'modules/course/course-configure-partial.html',
				label: "Edit Course"
			})
		.when ('/course/:courseId/user',
			{
				templateUrl: 'modules/classlist/classlist-view-partial.html',
				label: "Manage Users"
			})
		.when ('/course/:courseId/user/import',
			{
				templateUrl: 'modules/classlist/classlist-import-partial.html',
				label: "Import Users"
			})
		.when ('/course/:courseId/user/import/results',
			{
				templateUrl: 'modules/classlist/classlist-import-results-partial.html',
				label: "Results"
			})
		.when ('/course/:courseId/group/import',
		   {
				templateUrl: 'modules/group/group-import-partial.html',
				label: "Assign Groups"
		   })
		.when ('/course/:courseId/group/import/results',
			{
				templateUrl: 'modules/group/group-import-results-partial.html',
				label: "Results"
			})
		.when ('/course/:courseId/question/create', 
			{
				templateUrl: 'modules/question/question-create-partial.html',
				label: "Add Question"
			})
		.when ('/course/:courseId/question/:questionId', 
			{
				templateUrl: 'modules/question/question-view-partial.html',
				label: "View Question"
			})
		.when ('/course/:courseId/question/:questionId/edit',
			{
				templateUrl: 'modules/question/question-edit-partial.html',
				label: "Edit Question"
			})
		.when ('/course/:courseId/question/:questionId/answer/create', 
			{
				templateUrl: 'modules/answer/answer-create-partial.html',
				label: "Answer"
			})
		.when ('/course/:courseId/question/:questionId/answer/:answerId/edit',
			{
				templateUrl: 'modules/answer/answer-edit-partial.html',
				label: "Edit Answer"
			})
		.when ('/course/:courseId/question/:questionId/comment/create',
			{
				templateUrl: 'modules/comment/comment-question-create-partial.html',
				label: "Comment on Assignment"
			})
		.when ('/course/:courseId/question/:questionId/comment/:commentId/edit',
			{
				templateUrl: 'modules/comment/comment-question-edit-partial.html',
				label: "Edit Comment on Assignment"
			})
		.when('/course/:courseId/question/:questionId/answer/:answerId/comment/create',
			{
				templateUrl: 'modules/comment/comment-answer-create-partial.html',
				label: "Reply"
			})
		.when('/course/:courseId/question/:questionId/answer/:answerId/comment/:commentId/edit',
			{
				templateUrl: 'modules/comment/comment-answer-edit-partial.html',
				label: "Edit Reply"
			})
		.when ('/course/:courseId/question/:questionId/judgement', 
			{
				templateUrl: 'modules/judgement/judgement-partial.html',
				label: "Compare Answers"
			})
		.when('/course/:courseId/question/:questionId/selfevaluation',
			{
				templateUrl: 'modules/judgement/judgement-selfevaluation-partial.html',
				label: "Self-Evaluation"
			})
		.when ('/course/:courseId/question/:questionId/comparisons',
			   {
				   templateUrl: 'modules/comment/comment-judgement-partial.html',
				   label: "Comparisons"
			   })
		.when('/course/:courseId/question/:questionId/post/:postId',
			{
				templateUrl: 'modules/attachment/attachment-pdf-partial.html',
				label: "View Attachment"
			})
		.when('/course/:courseId/criterion/:criterionId/edit',
			{
				templateUrl: 'modules/criteria/criteria-configure-partial.html',
				label: "Edit Criterion"
		  	})
		.when('/report',{
				templateUrl: 'modules/report/report-create-partial.html',
				label: "Run Reports"
			})
		.when('/course/:courseId/gradebook',
			{
				templateUrl: 'modules/gradebook/gradebook-partial.html',
				label: "See Activity"
		  	})
		.when('/user/create',
			{
				templateUrl: 'modules/user/user-create-partial.html',
				label: "Create User"
			})
		.when('/user/:userId/edit',
			{
				templateUrl: 'modules/user/user-edit-partial.html',
				label: "Edit User"
			})
		.when('/user/:userId',
			{
				templateUrl: 'modules/user/user-view-partial.html',
				label: "View User"
			})
		.otherwise({redirectTo: '/'});
});
