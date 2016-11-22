Feature: View Home
  As user, I want to view courses on the home page

  Scenario: Loading home page as admin
    Given I'm a System Administrator
    And I'm on 'home' page
    Then I should see my courses with names:
      | name     |
      | CHEM 111 |
      | PHYS 101 |

  Scenario: Loading home page as instructor
    Given I'm an Instructor
    And I'm on 'home' page
    Then I should see my courses with names:
      | name     |
      | CHEM 111 |
      | PHYS 101 |

  Scenario: Filtering home page courses as instructor
    Given I'm an Instructor
    And I'm on 'home' page
    When I filter home page courses by 'CHEM'
    Then I should see '1' courses
    And I should see my courses with names:
      | name     |
      | CHEM 111 |

  Scenario: Loading home page as student
    Given I'm a Student
    And I'm on 'home' page
    Then I should see my courses with names:
      | name     |
      | CHEM 111 |
      | PHYS 101 |