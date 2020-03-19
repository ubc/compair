from abc import ABC, abstractmethod

class UserLookupMixin(ABC):

    @abstractmethod
    def get_by_username(self, username):
        pass

    @abstractmethod
    def get_by_student_number(self, stduent_number):
        pass
