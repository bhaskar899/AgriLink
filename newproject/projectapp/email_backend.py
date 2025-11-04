import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.utils.functional import cached_property


# This class overrides Django's default SSL context creation for SMTP.
# It specifically disables the VERIFY_X509_STRICT flag that causes the
# "Basic Constraints of CA cert not marked critical" error.

class CustomEmailBackend(SMTPBackend):

    @cached_property
    def ssl_context(self):
        # 1. Start with the default SSL context
        context = ssl.create_default_context()

        # 2. Load custom cert/key if provided
        if self.ssl_certfile or self.ssl_keyfile:
            context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)

        # 3. CRITICAL FIX: Check if the strict flag exists and disable it.
        # This fixes the 'Basic Constraints not marked critical' error.
        if hasattr(ssl, 'VERIFY_X509_STRICT'):
            context.verify_flags &= ~ssl.VERIFY_X509_STRICT

        return context