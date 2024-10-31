# v1.3

## Notable changes
* Many dependencies, both frontend and backend, were updated.

### New Features
* "Download All" attachments button was added to generate and download a zip file of all student submitted answer attachments. This can be found in an assignment's "Participation" tab under the "Attachments" column.
* The "Assignment End-Date" tool was added for admin users to query for the assignments end-date. 
  * The purpose of this page is to search for ongoing or active assignments on a given date, to help plan potential schedules for testing, staging, and production environments.

### New Environment Variables: For controlling worker memory leak
* CELERY_WORKER_MAX_TASKS_PER_CHILD - Kills a worker process and forks a new one when it has executed the given number of tasks. 

* CELERY_WORKER_MAX_MEMORY_PER_CHILD - Set to memory in kilobytes. Kills a worker process and forks a new one when it hits the given memory usage, the currently executing task will be allowed to complete before being killed. 

## Breaking Changes
Celery 4 introduced a new all lowercase environment variables system. ComPAIR
is now using this new system. To adapt a Celery environment variable to
ComPAIR, convert the original Celery variable to all uppercase and prefix it
"CELERY\_". ComPAIR will strip the prefix and lowercase the variable before
passing it to Celery. A few Celery environment variables were renamed in the
new system, the ones supported in ComPAIR are:

* CELERY_ALWAYS_EAGER is now CELERY_TASK_ALWAYS_EAGER
  * Set to true if running stock standalone, see `compair/settings.py`.
  * Set to false if running via repo's docker-compose.yml
* BROKER_TRANSPORT_OPTIONS  is now CELERY_BROKER_TRANSPORT_OPTIONS
* CELERYBEAT_SCHEDULE is now CELERY_BEAT_SCHEDULE

# v1.2.12

## Notable changes
* Add sending the submittedAt timestamp when sending grades via LTI 1.1

# v1.2.11

## Notable changes
* Fixed issues with learning events emitted while impersonating a user

# v1.2.10

## Notable changes
* Added LTI custom parameter sanitizer to LTI consumers

# v1.2.8

## Notable changes
* Fixed another issue around Learning record event retries

# v1.2.7

## Notable changes
* Fixed issues around Learning record event retries

# v1.2.4

## Notable changes
* Added inline error reporting for forms
* Fixed problems with MathJax

# v1.2.2

## Breaking changes

* xAPI statements emitted changed to more closely match Caliper events
* Renamed `XAPI_APP_BASE_URL` to `LRS_APP_BASE_URL`
* Renamed `LRS_STATEMENT_ENDPOINT` to `LRS_XAPI_STATEMENT_ENDPOINT`
* Renamed `LRS_AUTH` to `LRS_XAPI_AUTH`
* Renamed `LRS_USERNAME` to `LRS_XAPI_USERNAME`
* Renamed `LRS_PASSWORD` to `LRS_XAPI_PASSWORD`

## Notable changes

* Added support for transmitting Caliper events

# v1.2

## Breaking changes

* `CAS_LOGIN_ENABLED` is now disabled by default.
* Renamed `EXPOSE_CAS_USERNAME_TO_INSTRUCTOR` to `EXPOSE_THIRD_PARTY_USERNAMES_TO_INSTRUCTOR`
* Renamed `LRS_ACTOR_ACCOUNT_USE_CAS` to `LRS_ACTOR_ACCOUNT_USE_GLOBAL_UNIQUE_IDENTIFIER`
* Renamed `LRS_ACTOR_ACCOUNT_CAS_HOMEPAGE` to `LRS_ACTOR_ACCOUNT_GLOBAL_UNIQUE_IDENTIFIER_HOMEPAGE`
* The LTI Consumer field `user_id_override` functionality has changed. It is now called `global_unique_identifier_param` and stores the global unique identifier for the user in the `lti_user` table. This was changed for compatibility with LTI Assignment and Grade Services which requires the launch `user_id` which was previously being overwritten. All `lti_user` entries associated with LTI consumers that used `user_id_override` will automatically be removed. These users will have their accounts automatically re-linked the next time they launch from the LTI provider.

## Notable changes

* Improvements for automatic ComPAIR account creation and LTI account linking (when `global_unique_identifier` is configured)
* The ability to create group assignments, meaning students submit one answer per group but still complete required comparisons/self-evaluation individually
* The addition of a student view, which lets instructors preview the application from a specific student’s POV
* The option to use specific dates and customized instructions for the self-evaluation step
* Improvements to the layout and data in downloadable reports
* New course filters on the dashboard, so instructors can view just their upcoming, active, or current courses
* Updates to the look and content of the support site, including a new FAQ page
* A back end change allowing easier customization of the login text and buttons

For full list of changes: https://github.com/ubc/compair/issues?utf8=%E2%9C%93&q=milestone%3A%22Version%201.2%22%20

# v1.1.4

## Notable changes

* Added system level control over which profile fields students can change and automatic updating for these fields on login.

# v1.1

## Notable changes

* The addition of multidimensional scaling to the pair selection algorithm, meaning that answer pairs should be selected more accurately when multiple criteria are used
* Adding an option for instructors to include their own answers in assignments to see how students respond to and score/rank them (the latter applies only when the adaptive setting is used)
* Interface changes to improve the student experience (based on results from in-depth usability testing this fall)
* Most notably, more clearly labeling and indicating where to find peer feedback as well as showing completed student work over two tabs in each assignment (one labeled "Your Answer + Feedback" and the other "Your Comparisons")
* General updates to the mobile view of the application
* Removing assignment help comments (this tab will no longer need to be monitored by instructors or instructional teams)
* Sorting student work by last name on the "Comparisons" tab for easier grading
* Refining the consistency and readability of pop-up messages
* The ability for instructors to mark courses as test environments ("sandboxes")
* Improving the LTI integration (i.e., allowing ComPAIR to work more smoothly with other learning platforms like Canvas)
* New system settings for controlling the visibility of some private student data from instructor (default hides email and CAS username from instructor view/reports)

For full list of changes: https://github.com/ubc/compair/issues?utf8=%E2%9C%93&q=milestone%3A%22Version%201.1%22%20

# v1.0

## Notable changes

* A new location for comparisons, so instructors can view these on the assignment screen alongside answers, help comments, and participation (note: this means existing instructors will notice the absence of the green "See Comparisons" button on the course screen and can access comparisons instead by clicking on the hyperlinked number of comparisons below any assignment)
* Customizable weights for instructors using multiple criteria on an assignment
* The ability for instructors to duplicate assignments
* The option for instructors to customize the instructional text that appears to students prompting the peer feedback portion of the comparison
* Basic notification emails that, when enabled, let instructors know about new help comments and let students know about new replies to their answer
* Automatic embedding of certain multimedia URLS, so links from trusted sources appear in answers without having to be clicked (e.g., YouTube videos)
* Updates to the LTI integration, so ComPAIR can be used at UBC with Canvas
* A new downloadable report for instructors containing student feedback per assignment
* A logo and favicon (bookmark image) for the application
* Improvements to the ComPAIR support site, including the addition of a style guide to keep the application consistent as we grow

For full list of changes: https://github.com/ubc/compair/issues?utf8=%E2%9C%93&q=milestone%3A%22Version%201.0%22%20
