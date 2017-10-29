#!/usr/bin/env python

#
# Python API:
#
#   from aletheia import generate, sign, verify
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
import sys
from hashlib import sha512

import requests

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


class Aletheia:

    KEY_SIZE = 8192
    HOME = os.path.join(os.getenv("HOME"), ".aletheia")
    PRIVATE_KEY_PATH = os.path.join(HOME, "aletheia.pem")
    PRIVATE_KEY_NAME = "ALETHEIA_PRIVATE_KEY"
    PUBLIC_KEY_CACHE = os.path.join(HOME, "public-keys")

    @classmethod
    def generate(cls):

        path = cls.HOME
        os.makedirs(cls.HOME, exist_ok=True)

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

        signature = base64.encodebytes(self._get_private_key().sign(
            image_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )).strip()

        subprocess.call((
            "exiftool",
            "-ImageSupplierImageID={}".format(signature.decode("utf-8")),
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
            key_url = subprocess.check_output(
                ("exiftool", "-s", "-s", "-s", "-ImageSupplierID", "-"),
                stdin=f
            ).strip()
            f.seek(0)
            signature = base64.decodebytes(subprocess.check_output(
                ("exiftool", "-s", "-s", "-s", "-ImageSupplierImageID", "-"),
                stdin=f
            ).strip())
            f.seek(0)
            image_data = subprocess.check_output(
                ("exiftool", "-all=", "-"),
                stdin=f
            )

        self._get_public_key(key_url).verify(
            signature,
            image_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return True

    def _get_private_key(self):
        """
        Try to set the private key by either (a) pulling it from the
        environment, or (b) sourcing it from a file in a known location.
        """

        environment_key = os.getenv("ALETHEIA_PRIVATE_KEY")
        if environment_key:
            environment_key = bytes(environment_key.encode("utf-8"))
            if b"BEGIN RSA PRIVATE KEY" in environment_key.split(b"\n")[0]:
                return serialization.load_pem_private_key(
                     environment_key,
                     password=None,
                     backend=default_backend()
                )

        if os.path.exists(self.PRIVATE_KEY_PATH):
            with open(self.PRIVATE_KEY_PATH, "rb") as f:
                return serialization.load_pem_private_key(
                     f.read(),
                     password=None,
                     backend=default_backend()
                )

        raise RuntimeError(
            "You don't have a private key defined, so signing is currently "
            "impossible.  Either generate a key and store it at {} or put the "
            "key into an environment variable called {}.".format(
                self.PRIVATE_KEY_PATH,
                self.PRIVATE_KEY_NAME
            )
        )

    def _get_public_key(self, url):

        os.makedirs(self.PUBLIC_KEY_CACHE, exist_ok=True)

        cache = os.path.join(self.PUBLIC_KEY_CACHE, sha512(url).hexdigest())
        if os.path.exists(cache):
            with open(cache, "rb") as f:
                return serialization.load_pem_public_key(
                     f.read(),
                     backend=default_backend()
                )

        response = requests.get(url)
        if response.status_code == 200:
            if b"BEGIN PUBLIC KEY" in response.content:
                with open(cache, "wb") as f:
                    f.write(requests.get(url).content)
                return self._get_public_key(url)

        raise RuntimeError("The specified URL does not contain a public key")


def generate():
    Aletheia.generate()


def sign(path, public_key_url):
    Aletheia().sign(path, public_key_url)


def sign_bulk(paths, public_key_url):
    aletheia = Aletheia()
    for path in paths:
        aletheia.sign(path, public_key_url)


def verify(path):
    Aletheia().verify(path)


def verify_bulk(paths):
    aletheia = Aletheia()
    for path in paths:
        aletheia.verify(path)


class Command:

    def __init__(self):

        parser = argparse.ArgumentParser(prog="aletheia")
        parser.set_defaults(func=parser.print_help)
        subparsers = parser.add_subparsers(dest="subcommand")

        subparsers.add_parser(
            "generate",
            help="Generate a public/private key pair for use in siging & 3rd "
                 "party verification. (Do this first)"
        )

        parser_sign = subparsers.add_parser("sign", help="Sign a file")
        parser_sign.add_argument("path")
        parser_sign.add_argument("url")

        parser_verify = subparsers.add_parser(
            "verify", help="Verify the origin of a file")
        parser_verify.add_argument("path")

        args = parser.parse_args()

        try:
            if args.subcommand:
                getattr(self, args.subcommand)(args)
            else:
                parser.print_help()
        except (RuntimeError, FileNotFoundError) as e:
            print(e, file=sys.stdout)
            sys.exit(1)

        sys.exit(0)

    @classmethod
    def generate(cls, *args):
        print("Generating private/public key pair...")
        generate()
        print("""
            All finished!
            
            You now have two files: aletheia.pem (your private key) and
            aletheia.pub (your public key).  Keep the former private, and share
            the latter far-and-wide.  Importantly, place your public key at a
            publicly accessible URL so that when you sign a file with your
            private key, it can be verified by reading the public key at that
            URL.
        """.replace("            ", ""))

    @classmethod
    def sign(cls, args):
        print("Signing {} with your private key".format(args.path))
        sign(args.path, args.url)
        sys.exit(0)

    @classmethod
    def verify(cls, args):
        try:
            verify(args.path)
        except InvalidSignature:
            print("There's something wrong with that file")
            sys.exit(1)

        print("The file appears to be legit")
        sys.exit(0)


if __name__ == "__main__":
    Command()
