Feature: Edit Course Users
  As user, I want to manage the users of a course

  Scenario: Loading manage course users page as admin
    Given I'm a System Administrator
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I select the 'Manage Users' button
    Then I should be on the 'manage users' page

  Scenario: Loading manage course users page as instructor
    Given I'm an Instructor
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I select the 'Manage Users' button
    Then I should be on the 'manage users' page
    And I should see '2' users listed for the course
    And I should see course users with displaynames:
      | displayname           |
      | First Instructor      |
      | First Student         |

  Scenario: Adding user to course as admin
    Given I'm a System Administrator
    And I'm on 'edit course user' page for course with id '1abcABC123-abcABC123_Z'
    When I fill form item '$ctrl.user' in with 'Second'
    And I select the first user search result
    And I select the Student role for the user
    And I submit form with the 'Enrol' button
    Then I should see '3' users listed for the course
    And I should see course users with displaynames:
      | displayname            |
      | First Student          |
      | Second Student         |
      | root                   |

  Scenario: Sorting course users as instructor
    Given I'm an Instructor
    And I'm on 'edit course user' page for course with id '1abcABC123-abcABC123_Z'
    When I sort by displayname in decending order
    Then I should see course users with displaynames:
      | displayname            |
      | First Student          |
      | First Instructor       |

  Scenario: Removing user from course as instructor
    Given I'm an Instructor
    And I'm on 'edit course user' page for course with id '1abcABC123-abcABC123_Z'
    When I drop the second user from the course
    Then I should see '1' users listed for the course
    And I should see course users with displaynames:
      | displayname            |
      | First Instructor       |

  Scenario: Changing user's group in course as instructor
    Given I'm an Instructor
    And I'm on 'edit course user' page for course with id '1abcABC123-abcABC123_Z'
    When I select the Instructor role for the second user
    Then I should see a success message

  Scenario: Changing user's group in course as instructor
    Given I'm an Instructor
    And I'm on 'edit course user' page for course with id '1abcABC123-abcABC123_Z'
    When I set the second user's group to 'Second Group'
    Then I should see a success message

  Scenario: Removing user from group in course as instructor
    Given I'm an Instructor
    And I'm on 'edit course user' page for course with id '1abcABC123-abcABC123_Z'
    When I set the second user's group to '- None -'
    Then I should see a success message


