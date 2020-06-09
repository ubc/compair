from sqlalchemy.ext.declarative import declared_attr

from compair.core import db

class DefaultTableMixin(db.Model):
    __abstract__ = True

    default_table_args = {
        'mysql_charset': 'utf8mb4',
        'mysql_engine': 'InnoDB',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    __table_args__ = default_table_args

    id = db.Column(db.Integer, primary_key=True, nullable=False)