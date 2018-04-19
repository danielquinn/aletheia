# Aletheia
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aletheia.svg)](https://pypi.org/project/aletheia/)

Fight fake news with cryptographic signatures

Aletheia uses public key signing techniques in an effort to combat fake news.
The idea is that rather than employing expensive AI techniques to detect fakes,
we can leverage existing human-based networks of trust and use cryptography to
sign images, audio, and video so that **trust** becomes associated with the
*origin of the file* rather than its content.

To that end, we sign all media we produce so that it can be verified as coming 
from us.  After that, it's only our personal (or professional) reputations that
can be called into question.

This is further outlined in this [blog post](https://danielquinn.org/blog/public-key-authentication-for-media-files-why-isnt-this-a-thing/)
on the subject.  This project is inspired by this [Radiolab story](http://futureoffakenews.com/videos.html)
covering how surprisingly easy it is to create believable audio & video fakes.

## Visuals

### Signing

This is a typical media file

![A basic file](presentation/img/diagrams/sign-structure.png)

Aletheia uses your private key to sign the relevant portion of the file:

![Signing with a private key](presentation/img/diagrams/sign-read.png)

That signature is inserted into the file header, along with the URL for the
public key:

![Writing the headers](presentation/img/diagrams/sign-write.png)

The final result is a slightly larger file, now with a means of verifying its
origin.

![A basic file](presentation/img/diagrams/sign-final.png)

### Verification

When it comes time to verify the file, you only need to extract the public key
URL:

![Extract the public key URL](presentation/img/diagrams/verify-extract.png)

...and fetch that key from the creator's site:

![Fetch the public key](presentation/img/diagrams/verify-fetch.png)

Finally, we use the public key to verify the file:

![Verify all the things!](presentation/img/diagrams/verify-final.png)

Aletheia will do all of this for you in two commands: `sign`, and `verify`.


## A technical explanation

The process is relatively simple: source organisations & individuals can
publish their public key somewhere on the internet and use their private key to
sign the media they distribute.  Social networks and individuals can then
reference this signature to verify the origin.

### Signing your media files

#### Generate a private & public key

Generating a private & public key is necessary for the signing & verification
process, but this only needs to be run once.

```bash
$ aletheia generate
Generating private/public key pair...

All finished!

You now have two files: aletheia.pem (your private key) and
aletheia.pub (your public key).  Keep the former private, and share
the latter far-and-wide.  Importantly, place your public key at a
publicly accessible URL so that when you sign a file with your
private key, it can be verified by reading the public key at that
URL.
```

#### Generate a signature

```bash
$ aletheia sign file.jpg https://example.com/my-public-key.pub
```

Here, the `aletheia` program:

1. Gets the image data (sans metadata)
2. Signs it with our private key
3. Converts the signature to text
4. Writes the new signature to the file along with the location of our public
   key.

#### Verifying your media files

```bash
$ aletheia verify file.jpg
```

Much like signing, `aletheia` is doing all the work for you:

1. It extracts the signature & URL from the file
2. Fetches the public key from the URL & caches it
3. Attempts to verify the signature on the file with said public key.


## Project Status

Aletheia is working, and ready to be deployed on sites running Python, or ones
happy to use the Python-based command-line script.  In order for it to be
widely adopted however, more needs to be done.  Here's what we have so far:

### Ready

We now have a working [Python library](https://pypi.org/project/aletheia/) that
can generate keys as well as support the following file formats:

Format | Sign  | Verify
------ | :---: | :---:
JPEG   | 👍 | 👍
MP3    | 👍 | 👍
GIF    | ❌    | ❌
MKV    | ❌    | ❌
MP4    | ❌    | ❌


### Help Wanted

#### Support for additional formats.

The lowest-hanging fruit, JPEG images & MP3s are finished, so now the
priorities are the other popular web formats like `gif`, `mkv`, `webm`, and
`mp4` -- assuming these formats have a metadata layer into which we can include
a signature.

#### Whitepaper

This project has working code & tests, but lacks a proper spec outlining what's
required for compliance -- the sort of document other developers might follow
to port the functionality to other languages.  *I could really use some help on
this from someone with some experience in this area*.

#### Porting the Python library to additional languages

Python is great, but it's not for everyone.  Ideally, it would great if
developers in languages like Ruby, Javascript, PHP, Java, Rust, Clojure, Go,
and C# could use aletheia in their chosen environment.
