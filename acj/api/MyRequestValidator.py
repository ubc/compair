from oauthlib.oauth1 import RequestValidator

class MyRequestValidator(RequestValidator):
    #key = Yz2klFFzAdH0wVBTHF9YpUjeYpKt2C
    #secret = j0yrtshr4uKY9hmdM2xdYst0roDhHw
    enforce_ssl = False
    def validate_timestamp_and_nonce(self, timestamp, nonce, request,
                                        request_token=None,
                                        access_token=None):
        return True
    def validate_client_key(self, client_key, request):
        return True
    def get_client_secret(self, client_key, request):
        return u"j0yrtshr4uKY9hmdM2xdYst0roDhHw"
