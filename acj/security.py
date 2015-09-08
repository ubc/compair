from passlib.apps import custom_app_context
from passlib.context import CryptContext

default = custom_app_context

plaintext = CryptContext(
    schemes=["plaintext"],
    default="plaintext",
)
