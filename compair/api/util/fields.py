# define commonly used webargs stuff for fields

from webargs import fields, validate

# validators
not_empty = validate.Length(min=1)

# commonly used fields
pagination_fields = {
    'page': fields.Int(missing=1, required=False),
    'perPage': fields.Int(missing=20, required=False)
}
