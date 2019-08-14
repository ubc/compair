// Provides the services and controllers for Student View

(function() {

var module = angular.module('ubc.ctlt.compair.studentview',
    [
        'ngResource',
        'ubc.ctlt.compair.common.form',
        'ubc.ctlt.compair.course',
        'ubc.ctlt.compair.toaster'
    ]
);

module.controller(
    "StudentViewController",
    [ "$scope", "UserResource", "ClassListResource", "Session", "$uibModalInstance", "Toaster",
    function($scope, UserResource, ClassListResource, Session, $uibModalInstance, Toaster) {
        $scope.studentView = $scope.studentView || {};

        $scope.submitted = false;
        $scope.studentView.courseId = $scope.currentCourseId;
        $scope.studentView.userId = null;
        UserResource.getTeachingUserCourses().$promise.then(function(ret) {
            $scope.courses = ret.courses;
        });
        $scope.getClassList = function() {
            if ($scope.studentView.courseId) {
                ClassListResource.get({'courseId': $scope.studentView.courseId}).$promise.then(function (ret) {
                    $scope.classlist = ret.objects;
                });
            } else {
                $scope.classlist = [];
            }
        }
        $scope.getClassList();
        $scope.saveViewAttempted = false;;
        
        // decide on showing inline errors
        $scope.showErrors = function($event, formValid) {

            // show error if invalid form
            if (!formValid) {
                
                // don't submit
                $event.preventDefault();
                
                // set helper text and Toast
                $scope.helperMsg = "Sorry, this student view couldn't be loaded yet, but you're almost there. Simply update any highlighted information above and then try again.";
                $scope.helperTstrTitle = "Sorry, this student view couldn't be loaded yet";
                $scope.helperTstrMsg = "...but you're almost there. Simply update the highlighted information and then try again.";
                
                // display messages
                $scope.saveViewAttempted = true;
                Toaster.warning($scope.helperTstrTitle, $scope.helperTstrMsg);
            } else {
                
                $scope.studentViewSubmit();
            
            }
            
        };

        $scope.studentViewSubmit = function() {
            $scope.submitted = true;

            var studentView = $scope.studentView || {};
            Session
                .impersonate(studentView.courseId, studentView.userId)
                .then(function() {
                    $uibModalInstance.close($scope.studentView);
                }, function() {
                    $scope.submitted = false;
                });

            Toaster.success("Student View Enabled", 'You are now viewing ComPAIR as a student.');
        };
    }
]);



})();