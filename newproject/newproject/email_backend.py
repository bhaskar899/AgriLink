import ssl
import smtplib

from django.core.mail.backends.smtp import EmailBackend


class CustomEmailBackend(EmailBackend):

    def open(self):
        """
        Open a network connection — SSL certificate verify disabled
        """
        if self.connection:
            return False

        try:
            # Create SSL-bypass context
            context = ssl._create_unverified_context()

            # Create SMTP connection manually
            self.connection = smtplib.SMTP(self.host, self.port)
            self.connection.ehlo()
            if self.use_tls:
                self.connection.starttls(context=context)
                self.connection.ehlo()

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True

        except Exception:
            if not self.fail_silently:
                raise

        return False