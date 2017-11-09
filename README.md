# Aletheia

A means of signing media files

Leverage public key signing techniques in an effort to combat fake news.  The
idea is that images, audio, and video should not be considered "trusted" unless
their source is both verifiable and trustworthy.

To that end, we sign all media we produce so that it can be verified as coming 
from us.  After that, it's only our personal (or professional) reputations that
can be called into question.

This is further outlined in this [blog post](https://danielquinn.org/blog/public-key-authentication-for-media-files-why-isnt-this-a-thing/)
on the subject.  This project is inspired by this [Radiolab story](http://futureoffakenews.com/videos.html)
covering how surprisingly easy it is to create believable audio & video fakes.

## A technical explanation

The process is relatively simple: source organisations & individuals can
publish their public key somewhere on the internet and use their private key to
sign the media they distribute.  Social networks and individuals can then
reference this signature to verify the origin.

For static images, this can all be done with the excellent [Exiftool](https://sno.phy.queensu.ca/~phil/exiftool/)
utility coupled with [GPG](https://www.gnupg.org/):

### Signing your media files

#### Generate a private & public key

Generating a private & public key is necessary for the signing & verification
process, but thiis only needs to be run once.

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

Here we use Exiftool to get the image data (sans metadata), sign it with our,
private key, convert the signature to base64, and again use Exiftool to write
the new signature to the file along with the location of our public key

### Verifying your media files

```bash
$ aletheia verify file.jpg
```

This extracts the signature & URL from the file, fetches the public key from
the URL, caches it, and then attempts to verify the signature on the file with
said public key.


## Roadmap

This is meant to be a collaborative project, since frankly, I don't have all of
the skills required to make this work on as broad a scale as I'd like it to.

1. A [proof of concept](https://github.com/danielquinn/aletheia/tree/master/proof-of-concept)
   using GPG and a couple Bash scripts ✅
2. A fully functional [Python library](https://github.com/danielquinn/pyletheia/)
   that can:
    * Create a pair of keys or use existing ones ✅
    * Sign a JPEG image ✅
    * Verify a signed JPEG image ✅
3. Support additional formats.  High priorities include `gif`, `png`, `mkv`,
   `mp4`, and `mp3` -- assuming these formats have a metadata layer into which
   we can include a signature.
4. A proper spec outlining what's required for compliance.  *I could really use
   some help on this from someone with some experience in this area*.
5. Invite others to write their own libraries in other languages/frameworks.
   Ideally, I'd like to see Aletheia implemented in Python, Ruby, Javascript,
   PHP, Java, Rust, Clojure, and Go.
