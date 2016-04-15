Feature: View Profile
  As user, I want to view profiles of users

  Scenario: Loading own profile as admin
    Given I'm "admin"
    And I'm on "home" page
    When I select "Profile" button
    Then I should be on the "profile" page
    And I should see text:
      | locator                     | text                  |
      | h1                          | root's Profile        |
      | #user_system_role           | System Administrator  |
      | #user_username              | root                  |
      | #user_student_no            |                       |
      | #user_fullname              | JaNy bwsV             |
      | #user_displayname           | root                  |
      | #user_email                 |                       |
      | #edit-profile-btn           | Edit                  |
    And I should see:
      | locator                     |
      | #user_avatar                |
      | #user_lastonline            |
      
  # TODO: add steps to get to other user's profile page without direct link
  Scenario: Loading other user's profile as admin
    Given I'm "admin"
    And I'm on "user" page for user with id "2"
    Then I should see text:
      | locator                     | text                          |
      | h1                          | First Instructor's Profile    |
      | #user_system_role           | Instructor                    |
      | #user_username              | instructor1                   |
      | #user_student_no            |                               |
      | #user_fullname              | First Instructor              |
      | #user_displayname           | First Instructor              |
      | #user_email                 | first.instructor@exmple.com   |
      | #edit-profile-btn           | Edit                          |
    And I should see:
      | locator                     |
      | #user_avatar                |
      | #user_lastonline            |
  
  Scenario: Loading own profile as instructor
    Given I'm "instructor1"
    And I'm on "home" page
    When I select "Profile" button
    Then I should be on the "profile" page
    And I should see text:
      | locator                     | text                          |
      | h1                          | First Instructor's Profile    |
      | #user_system_role           | Instructor                    |
      | #user_username              | instructor1                   |
      | #user_student_no            |                               |
      | #user_fullname              | First Instructor              |
      | #user_displayname           | First Instructor              |
      | #user_email                 | first.instructor@exmple.com   |
      | #edit-profile-btn           | Edit                          |
    And I should see:
      | locator                     |
      | #user_avatar                |
      | #user_lastonline            |
      
  # TODO: add steps to get to other user's profile page without direct link
  Scenario: Loading other user's profile as instructor with edit permissions
    Given I'm "instructor1"
    And I'm on "user" page for user with id "3"
    Then I should see text:
      | locator                     | text                          |
      | h1                          | First Student's Profile       |
      | #user_system_role           | Student                       |
      | #user_username              | student1                      |
      | #user_student_no            |                               |
      | #user_fullname              | First Student                 |
      | #user_displayname           | First Student                 |
      | #user_email                 | first.student@exmple.com      |
      | #edit-profile-btn           | Edit                          |
    And I should see:
      | locator                     |
      | #user_avatar                |
      | #user_lastonline            |

  # TODO: add steps to get to other user's profile page without direct link
  Scenario: Loading other user's profile as instructor without edit permissions
    Given I'm "instructor1"
    And I'm on "user" page for user with id "4"
    Then I should see text:
      | locator                     | text                          |
      | h1                          | Second Student's Profile      |
      | #user_system_role           | Student                       |
      | #user_username              | student2                      |
      | #user_student_no            |                               |
      | #user_fullname              | Second Student                |
      | #user_displayname           | Second Student                |
      | #user_email                 | second.student@exmple.com     |
    And I should see:
      | locator                     |
      | #user_avatar                |
      | #user_lastonline            |
    And I should not see "#edit-profile-btn" on the page


  Scenario: Loading own profile as student
    Given I'm "student1"
    And I'm on "home" page
    When I select "Profile" button
    Then I should be on the "profile" page
    And I should see text:
      | locator                     | text                          |
      | h1                          | First Student's Profile       |
      | #user_system_role           | Student                       |
      | #user_username              | student1                      |
      | #user_student_no            |                               |
      | #user_fullname              | First Student                 |
      | #user_displayname           | First Student                 |
      | #user_email                 | first.student@exmple.com      |
      | #edit-profile-btn           | Edit                          |
    And I should see:
      | locator                     |
      | #user_avatar                |
      | #user_lastonline            |

  # TODO: add steps to get to other user's profile page without direct link
  Scenario: Loading other user's profile as student
    Given I'm "student1"
    And I'm on "user" page for user with id "2"
    Then I should see text:
      | locator                     | text                          |
      | h1                          | First Instructor's Profile    |
      | #user_displayname           | First Instructor              |
    And I should see:
      | locator                     |
      | #user_avatar                |
      | #user_lastonline            |
    And I should not see:
      | locator                     |
      | #user_system_role           |
      | #user_username              |
      | #user_student_no            |
      | #user_fullname              |
      | #user_email                 |
      | #edit-profile-btn           |