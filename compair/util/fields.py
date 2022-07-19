# define commonly used webargs fields

from webargs import fields, validate

pagination_fields = {
    'page': fields.Int(missing=1, required=False),
    'perPage': fields.Int(missing=20, required=False)
}
