Feature: View Course
  As user, I want to view a course

  Scenario: Loading course page as admin
    Given I'm a System Administrator
    And I'm on 'home' page
    When I select the course named 'CHEM 111'
    Then I should be on the 'course' page
    And I should see '6' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment Upcoming          |
      | Assignment Being Answered    |
      | Assignment With Draft Answer |
      | Assignment Being Compared    |
      | Assignment Finished          |
      | Assignment With Feedback     |

  Scenario: Loading course page as instructor
    Given I'm an Instructor
    And I'm on 'home' page
    When I select the course named 'CHEM 111'
    Then I should be on the 'course' page
    And I should see '6' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment Upcoming          |
      | Assignment Being Answered    |
      | Assignment With Draft Answer |
      | Assignment Being Compared    |
      | Assignment Finished          |
      | Assignment With Feedback     |

  Scenario: Filtering assignments on course page as instructor
    Given I'm an Instructor
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I filter course page assignments by 'Assignments being answered'
    Then I should see '2' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment Being Answered    |
      | Assignment With Draft Answer |

  Scenario: Filtering assignments on course page as instructor
    Given I'm an Instructor
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I filter course page assignments by 'Assignments being compared'
    Then I should see '1' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment Being Compared    |

  Scenario: Filtering assignments on course page as instructor
    Given I'm an Instructor
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I filter course page assignments by 'Upcoming assignments'
    Then I should see '1' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment Upcoming          |


  Scenario: Loading course page as student
    Given I'm a Student
    And I'm on 'home' page
    When I select the course named 'CHEM 111'
    Then I should be on the 'course' page
    And I should see '5' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment Being Answered    |
      | Assignment With Draft Answer |
      | Assignment Being Compared    |
      | Assignment Finished          |
      | Assignment With Feedback     |

  Scenario: Sorting assignments on course page as student
    Given I'm a Student
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I sort course page assignments by 'Assignment start date'
    Then I should see '5' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment Being Answered    |
      | Assignment With Draft Answer |
      | Assignment Being Compared    |
      | Assignment Finished          |
      | Assignment With Feedback     |

  Scenario: Sorting assignments on course page as student
    Given I'm a Student
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I sort course page assignments by 'Answer due date'
    Then I should see '5' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment Finished          |
      | Assignment Being Compared    |
      | Assignment Being Answered    |
      | Assignment With Draft Answer |
      | Assignment With Feedback     |

  Scenario: Sorting assignments on course page as student
    Given I'm a Student
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I sort course page assignments by 'Comparisons due date'
    Then I should see '5' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment With Draft Answer |
      | Assignment Finished          |
      | Assignment Being Compared    |
      | Assignment Being Answered    |
      | Assignment With Feedback     |

  Scenario: Filtering assignments on course page as student
    Given I'm a Student
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I filter course page assignments by 'My unfinished assignments'
    Then I should see '3' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment Being Answered    |
      | Assignment With Draft Answer |
      | Assignment Being Compared    |

  Scenario: Filtering assignments on course page as student
    Given I'm a Student
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I filter course page assignments by 'Assignments with drafts'
    Then I should see '1' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment With Draft Answer |

  Scenario: Filtering assignments on course page as student
    Given I'm a Student
    And I'm on 'course' page for course with id '1abcABC123-abcABC123_Z'
    When I filter course page assignments by 'Assignments with feedback'
    Then I should see '1' assignments
    And I should see my assignments with names:
      | name                         |
      | Assignment With Feedback     |
