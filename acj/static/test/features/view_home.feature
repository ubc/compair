Feature: View Home
  As user, I want to view courses on the home page

  Scenario: Loading home page as admin
    Given I'm "admin"
    And I'm on "home" page
    Then I should see my courses with names:
      | name               |
      | Test Course 1      |
      | Test Course 2      |

  Scenario: Filtering home page courses as admin
    Given I'm "admin"
    And I'm on "home" page
    Then I should see "2" courses
    And I should see my courses with names:
      | name               |
      | Test Course 1      |
      | Test Course 2      |
    When I filter home page courses by "Course 1"
    Then I should see "1" courses
    And I should see my courses with names:
      | name               |
      | Test Course 1      |

  Scenario: Loading home page as instructor
    Given I'm "instructor1"
    And I'm on "home" page
    Then I should see my courses with names:
      | name               |
      | Test Course 1      |
      | Test Course 2      |

  Scenario: Filtering home page courses as instructor
    Given I'm "instructor1"
    And I'm on "home" page
    Then I should see "2" courses
    And I should see my courses with names:
      | name               |
      | Test Course 1      |
      | Test Course 2      |
    When I filter home page courses by "Course 1"
    Then I should see "1" courses
    And I should see my courses with names:
      | name               |
      | Test Course 1      |

  Scenario: Loading home page as student
    Given I'm "student1"
    And I'm on "home" page
    Then I should see my courses with names:
      | name               |
      | Test Course 1      |
      | Test Course 2      |