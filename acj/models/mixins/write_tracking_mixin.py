from acj.core import db
from .create_tracking_mixin import CreateTrackingMixin
from .modify_tracking_mixin import ModifyTrackingMixin

class WriteTrackingMixin(ModifyTrackingMixin, CreateTrackingMixin):
    __abstract__ = True
