var myApp = angular.module('myApp', ['ngResource']);

myApp.factory('judgeFactory', function($resource) {
	return $resource( 'http://localhost\\:5000/script/:scriptId' );
});

myApp.config( function ($routeProvider) {
	$routeProvider
		.when ('/', 
			{
				controller: IndexController,
				templateUrl: 'intro.html'
			})
		.when ('/judgepage',
			{
				controller: JudgepageController,
				templateUrl: 'judgepage.html'
			})
		.when ('/login',
			{
				controller: UserController,
				templateUrl: 'login.html'
			})
		.otherwise({redirectTo: '/'});
});

function IndexController($scope) {
	;
}

function JudgepageController($scope, judgeFactory) {
	var idl = 1;
	var idr = 2;
	var winner;
	var script1 = judgeFactory.get( {scriptId:idl}, function() {
		content = script1.content;
		$scope.scriptl = content;
	});
	var script2 = judgeFactory.get( {scriptId:idr}, function() {
		content = script2.content;
		$scope.scriptr = content;
	});
	$scope.submit = function() {
		if ($scope.pick == 'left') {
			winner = idl;
		} else if ($scope.pick == 'right') {
			winner = idr;
		} else {
			alert('Pick a side');
			return;
		}
		alert('i am here');
		alert(winner);
		var temp = judgeFactory.save( {scriptId:winner}, function() {
			alert(temp.msg);
			window.location = "http://localhost:5000/static/index.html";
		});
	}
}

function UserController($scope) {
	;
}
