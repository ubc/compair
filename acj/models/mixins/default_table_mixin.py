from sqlalchemy.ext.declarative import declared_attr

from acj.core import db

class DefaultTableMixin(db.Model):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    default_table_args = {
        'mysql_charset': 'utf8',
        'mysql_engine': 'InnoDB',
        'mysql_collate': 'utf8_unicode_ci'
    }

    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)