from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime

class sql_utcnow(expression.FunctionElement):
    """ Custom sqlalchemy function to get UTC timestamp.
    reference: https://docs.sqlalchemy.org/en/latest/core/compiler.html#utc-timestamp-function
    """
    type = DateTime()

@compiles(sql_utcnow, 'postgresql')
def postgresql_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"

@compiles(sql_utcnow, 'mssql')
def mssql_utcnow(element, compiler, **kw):
    return "GETUTCDATE()"

@compiles(sql_utcnow, 'sqlite')
def sqlite_utcnow(element, compiler, **kw):
    return "DATETIME('NOW')"

@compiles(sql_utcnow, 'mysql')
def msql_utcnow(element, compiler, **kw):
    return "UTC_TIMESTAMP()"