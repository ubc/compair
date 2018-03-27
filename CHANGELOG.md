# v1.2

## Breaking changes

* `CAS_LOGIN_ENABLED` is now disabled by default.
* Renamed `LRS_ACTOR_ACCOUNT_USE_CAS` to `LRS_ACTOR_ACCOUNT_USE_THIRD_PARTY`
* Renamed `LRS_ACTOR_ACCOUNT_CAS_HOMEPAGE` to `LRS_ACTOR_ACCOUNT_THIRD_PARTY_HOMEPAGE`
* Renamed `EXPOSE_CAS_USERNAME_TO_INSTRUCTOR` to `EXPOSE_THIRD_PARTY_USERNAMES_TO_INSTRUCTOR`

## Notable changes

...

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
