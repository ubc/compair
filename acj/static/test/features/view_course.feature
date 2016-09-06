Feature: View Course
  As user, I want to view a course

  Scenario: Loading course page as admin
    Given I'm a System Administrator with assignments
    And I'm on 'home' page
    When I select the course named 'CHEM 111'
    Then I should be on the 'course' page
    And I should see '4' assignments
    And I should see my assignments with names:
      | name                      |
      | Assignment Finished       |
      | Assignment Being Compared |
      | Assignment Being Answered |
      | Assignment Upcoming       |

  Scenario: Loading course page as instructor
    Given I'm an Instructor with assignments
    And I'm on 'home' page
    When I select the course named 'CHEM 111'
    Then I should be on the 'course' page
    And I should see '4' assignments
    And I should see my assignments with names:
      | name                      |
      | Assignment Finished       |
      | Assignment Being Compared |
      | Assignment Being Answered |
      | Assignment Upcoming       |

  Scenario: Filtering assignments on course page as instructor
    Given I'm an Instructor with assignments
    And I'm on 'course' page for course with id '1'
    When I filter course page assignments by 'Assignments being answered'
    Then I should see '1' assignments
    And I should see my assignments with names:
      | name                      |
      | Assignment Being Answered |

  Scenario: Filtering assignments on course page as instructor
    Given I'm an Instructor with assignments
    And I'm on 'course' page for course with id '1'
    When I filter course page assignments by 'Assignments being compared'
    Then I should see '1' assignments
    And I should see my assignments with names:
      | name                      |
      | Assignment Being Compared |

  Scenario: Filtering assignments on course page as instructor
    Given I'm an Instructor with assignments
    And I'm on 'course' page for course with id '1'
    When I filter course page assignments by 'Upcoming assignments'
    Then I should see '1' assignments
    And I should see my assignments with names:
      | name                      |
      | Assignment Upcoming       |


  Scenario: Loading course page as student
    Given I'm a Student with assignments
    And I'm on 'home' page
    When I select the course named 'CHEM 111'
    Then I should be on the 'course' page
    And I should see '3' assignments
    And I should see my assignments with names:
      | name                      |
      | Assignment Finished       |
      | Assignment Being Compared |
      | Assignment Being Answered |

  Scenario: Filtering assignments on course page as student
    Given I'm a Student with assignments
    And I'm on 'course' page for course with id '1'
    When I filter course page assignments by 'My pending assignments'
    Then I should see '2' assignments
    And I should see my assignments with names:
      | name                      |
      | Assignment Being Compared |
      | Assignment Being Answered |

