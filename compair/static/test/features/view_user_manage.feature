Feature: Manage User Courses
  As user, I want to manage user courses & accounts

  Scenario: Loading root's users & accounts page by Courses & Accounts link as admin
    Given I'm a System Administrator
    And I'm on 'users' page
    When I select the root's Courses & Accounts link
    Then I should be on the 'user manage' page
    And I should see '2' courses listed
    And I should see courses with names:
      | name     |
      | CHEM 111 |
      | PHYS 101 |
    And I should see '0' LTI connections listed
    And I should see '0' third party connections listed

  Scenario: Loading student's courses & accounts page by Courses & Accounts link as admin
    Given I'm a System Administrator
    And I'm on 'users' page
    When I select student1's Courses & Accounts link
    Then I should be on the 'user manage' page
    And I should see '1' courses listed
    And I should see courses with names:
      | name     |
      | CHEM 111 |
    And I should see '2' LTI connections listed
    And I should see LTI connections with entries:
      | consumer_key    | lti_user_id |
      | consumer_key_1  | 12345000001 |
      | consumer_key_1  | 12345000002 |
    And I should see '2' third party connections listed
    And I should see third party connections with entries:
      | type | id      |
      | CAS  | CAS0001 |
      | CAS  | CAS0002 |

  Scenario: Filter user courses & accounts page courses as admin
    Given I'm a System Administrator
    And I'm on 'user manage' page for user with id '1abcABC123-abcABC123_Z'
    When I filter user courses & accounts page courses by 'CHEM'
    Then I should see '1' courses listed
    And I should see courses with names:
      | name     |
      | CHEM 111 |

  Scenario: Drop user from course as admin
    Given I'm a System Administrator
    And I'm on 'user manage' page for user with id '1abcABC123-abcABC123_Z'
    When I select drop for the first course listed
    Then I should see '1' courses listed
    And I should see courses with names:
      | name     |
      | PHYS 101 |

  Scenario: Change user's course role as admin
    Given I'm a System Administrator
    And I'm on 'user manage' page for user with id '1abcABC123-abcABC123_Z'
    When I select the Student role for the first course
    Then I should see a success message

  Scenario: Changing user's group in course as instructor
    Given I'm a System Administrator
    And I'm on 'user manage' page for user with id '1abcABC123-abcABC123_Z'
    When I set the first course's group to 'Second Group'
    Then I should see a success message

  Scenario: Removing user from group in course as instructor
    Given I'm a System Administrator
    And I'm on 'user manage' page for user with id '1abcABC123-abcABC123_Z'
    When I set the first course's group to '- None -'
    Then I should see a success message

  Scenario: Unlink LTI user as admin
    Given I'm a System Administrator
    And I'm on 'user manage' page for user with id '3abcABC123-abcABC123_Z'
    When I select unlink for the first LTI connection listed
    Then I should see '1' LTI connections listed
    And I should see LTI connections with entries:
      | consumer_key    | lti_user_id |
      | consumer_key_1  | 12345000002 |

  Scenario: Delete third party user as admin
    Given I'm a System Administrator
    And I'm on 'user manage' page for user with id '3abcABC123-abcABC123_Z'
    When I select delete for the first third party connection listed
    Then I should see '1' third party connections listed
    And I should see third party connections with entries:
      | type | id      |
      | CAS  | CAS0002 |