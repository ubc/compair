Feature: Manage User Courses
  As user, I want to manage user courses

  Scenario: Loading view user courses page by Manage Courses link as admin
    Given I'm a System Administrator
    And I'm on 'users' page
    When I select the root's Manage Courses link
    Then I should be on the 'user courses' page
    And I should see '2' courses listed
    And I should see courses with names:
      | name     |
      | CHEM 111 |
      | PHYS 101 |

  Scenario: Filter user courses page as admin
    Given I'm a System Administrator
    And I'm on 'user courses' page for user with id '1abcABC123-abcABC123_Z'
    When I filter user courses page by 'CHEM'
    Then I should see '1' courses listed
    And I should see courses with names:
      | name     |
      | CHEM 111 |

  Scenario: Drop user from course as admin
    Given I'm a System Administrator
    And I'm on 'user courses' page for user with id '1abcABC123-abcABC123_Z'
    When I select drop for the first course listed
    Then I should see '1' courses listed
    And I should see courses with names:
      | name     |
      | PHYS 101 |

  Scenario: Change user's course role as admin
    Given I'm a System Administrator
    And I'm on 'user courses' page for user with id '1abcABC123-abcABC123_Z'
    When I select the Student role for the first course
    Then I should see a success message

  Scenario: Changing user's group in course as instructor
    Given I'm a System Administrator
    And I'm on 'user courses' page for user with id '1abcABC123-abcABC123_Z'
    When I set the first course's group to 'Second Group'
    Then I should see a success message

  Scenario: Removing user from group in course as instructor
    Given I'm a System Administrator
    And I'm on 'user courses' page for user with id '1abcABC123-abcABC123_Z'
    When I set the first course's group to '- None -'
    Then I should see a success message