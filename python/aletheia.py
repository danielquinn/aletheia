#!/usr/bin/env python

#
# Python API:
#
#   from alethia import generate, sign, verify
#
#   generate(path)
#   sign(path, key, public_key_url)
#   verify(path, key)
#
# Command line API:
#
#   $ aletheia generate path
#   $ aletheia sign /path/to/file /path/to/key
#   $ aletheia verify /path/to/file /path/to/key
#

import argparse
import base64
import os
import subprocess

from six import text_type

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey
)


class Aletheia:

    KEY_SIZE = 8192

    def __init__(self, private_key=None, public_key=None):

        self.private_key = None
        self.public_key = None

        if private_key:
            self._init_private_key(private_key)

        if public_key:
            self._init_public_key(public_key)

    def _init_private_key(self, key):
        if isinstance(key, RSAPrivateKey):
            self.private_key = key
        elif isinstance(key, text_type):
            if "BEGIN RSA PRIVATE KEY" in key.split("\n")[0]:
                self.private_key = serialization.load_pem_private_key(
                     key,
                     password=None,
                     backend=default_backend()
                )
        raise RuntimeError("The private key is not in a recognisable format")

    def _init_public_key(self, key):
        if isinstance(key, RSAPublicKey):
            self.public_key = key
        elif isinstance(key, text_type):
            if "BEGIN PUBLIC KEY" in key.split("\n")[0]:
                self.public_key = serialization.load_pem_public_key(
                     key,
                    backend=default_backend()
                )
        raise RuntimeError("The public key is not in a recognisable format")

    @classmethod
    def generate(cls, path):

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=cls.KEY_SIZE,
            backend=default_backend()
        )

        with open(os.path.join(path, "aletheia.pem"), "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(os.path.join(path, "aletheia.pub"), "wb") as f:
            f.write(private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

    def sign(self, path, public_key_url):

        if not os.path.exists(path):
            raise FileNotFoundError("Specified file doesn't exist")

        with open(path, "rb") as f:
            image_data = subprocess.check_output(
                ("exiftool", "-all=", "-"),
                stdin=f
            )

        signature = base64.encodebytes(self.private_key.sign(
            image_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        ))

        subprocess.call((
            "exiftool",
            "-ImageSupplierImageID={}".format(signature),
            "-overwrite_original",
            path
        ))
        subprocess.call((
            "exiftool",
            "-ImageSupplierID={}".format(public_key_url),
            "-overwrite_original",
            path
        ))

    def verify(self, path):

        if not os.path.exists(path):
            raise FileNotFoundError("Specified file doesn't exist")

        with open(path, "rb") as f:
            signature = subprocess.check_output(
                ("exiftool", "-s", "-s", "-s", "-ImageSupplierImageID"),
                stdin=f
            )
            f.seek(0)
            image_data = subprocess.check_output(
                ("exiftool", "-all=", "-"),
                stdin=f
            )

        self.public_key.verify(
            signature,
            image_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )


def generate(path):
    Aletheia.generate(path)


def sign(path, key, public_key_url):
    Aletheia(private_key=key).sign(path, public_key_url)


def verify(path, key):
    Aletheia(public_key=key).verify(path)


class Command:

    def __init__(self):

        parser = argparse.ArgumentParser()
        parser.add_argument("command", choices=("generate", "sign", "verify"))
        parser.add_argument("path")
        parser.parse_args()

        args = parser.parse_args()

        getattr(self, args.command)(args.path)

    def generate(self, path):
        print("Generating private/public key pair")
        Aletheia.generate(path)

    def sign(self, path):
        pass

    def verify(self, path):
        pass


if __name__ == "__main__":
    Command()
