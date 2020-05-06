db = DAL('sqlite://storage.sqlite')

from gluon.tools import *
from gluon import current

# store report requests for testing
db.define_table(
    'report_request',
    Field('key', 'string', length=36),
    Field('report_definition', 'text', notnull=True),
    Field('data', 'text', notnull=True),
    Field('is_test_data', 'boolean', notnull=True),
    Field('pdf_file', 'blob'),
    Field('pdf_file_size', 'integer'),
    Field('created_on', 'datetime', notnull=True))

# store report definition for our album report
db.define_table(
    'report_definition',
    Field('report_definition', 'json', notnull=True),
    Field('report_type', 'string', length=30, notnull=True),
    Field('remark', 'text'),
    Field('last_modified_at', 'datetime', notnull=True))

db.define_table(
    'album',
    Field('name', 'string', length=100, notnull=True),
    Field('artist', 'string', length=100, notnull=True),
    Field('year', 'integer'),
    Field('best_of_compilation', 'boolean', notnull=True, default=False))
