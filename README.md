# Aletheia

A proof-of-concept for signing media files

This is an attempt to leverage public key signing techniques in an effort to
combat fake news.  The idea is that images, audio, and video should not be 
considered "trusted" unless their source is both verifiable and trustworthy.

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

#### Generate a signature

```bash
signature=$(cat file.jpg \
  | exiftool -all= - \
  | gpg --output - --detach-sign - \
  | base64 -w 0 \
  | xargs)
```

Here we use Exiftool to get the image data (sans metadata), sign it with GPG,
convert it to base64 so we can later write it to the file, and then use `xargs`
to strip the surrounding white space.

#### Write that signature to the media file

```bash
exiftool -ImageSupplierImageID=${signature} file.jpg
```

#### Write the URL to your public key to the media file

```bash
exiftool -ImageSupplierID=https://example.com/aletheia.pub file.jpg
```

### Verifying your media files

#### Get the signatures

```bash
$ cat file.jpg \
  | exiftool -s -s -s -ImageSupplierImageID - \
  | base64 -d \
  > file.sig
```

#### Get the public key

```bash
$ curl $(cat file.jpg | exiftool -s -s -s -ImageSupplierID -) > example.com.pub
$ gpg --import example.com.pub
```

#### Verify the file

```bash
$ cat file.jpg \
  | exiftool -all= - \
  | gpg --verify file.sig -
```


## Roadmap

This is meant to be a collaborative project, since frankly, I don't have all of
the skills required to make this work on as broad a scale as I'd like it to.

1. A proof of concept using GPG and a couple Bash scripts ✅
2. A fully functional Python library that can:
    * Create a pair of keys or use existing ones
    * Sign a JPEG image
    * Verify a signed JPEG image
3. Support additional formats.  High priorities include `gif`, `png`, `mkv`,
   `mp4`, and `mp3` -- assuming these formats have a metadata layer into which
   we can include a signature.
4. A proper spec outlining what's required for compliance.  *I could really use
   some help on this from someone with some experience in this area*.
5. Invite others to write their own libraries in other languages/frameworks.
   Ideally, I'd like to see Alethia implemented in Python, Ruby, Javascript,
   PHP, Rust, and Go.
