import base64

from cryptography.hazmat.primitives import serialization
from django.core.management.base import BaseCommand
from py_vapid import Vapid


class Command(BaseCommand):
    help = "Generate a VAPID keypair for Web Push and print settings.py values."

    def handle(self, *args, **options):
        vapid = Vapid()
        vapid.generate_keys()

        private_pem = vapid.private_pem().decode()

        public_raw = vapid.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        public_b64 = base64.urlsafe_b64encode(public_raw).rstrip(b'=').decode()

        self.stdout.write(self.style.SUCCESS("Paste this into settings.py:\n"))
        self.stdout.write("VAPID_PUBLIC_KEY = %r\n" % public_b64)
        self.stdout.write('VAPID_PRIVATE_KEY = """%s"""\n' % private_pem)
        self.stdout.write('VAPID_CLAIMS = {"sub": "mailto:admin@yourdomain.com"}\n')
        self.stdout.write(
            self.style.WARNING(
                "\nKeep VAPID_PRIVATE_KEY secret. VAPID_PUBLIC_KEY is sent to the browser (safe)."
            )
        )