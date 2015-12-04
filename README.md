# debs

For building your .debs.

This is a wrapper around sbuild and dput, but it automates it all for you.

## Config

See [misc/debsrc.ini](misc/debsrc.ini).

Configuration files live in ~/.debs/debsrc and in each directory. The
directory-local configs override the user configs.

## Installing debs

1. Add `deb http://deb.stoney.io/ testing/` to your `sources.list`.
1. Install the archive keys: `sudo apt-get install stoney.io-archive-keyring`
1. `sudo aptitude install debs`

## Todo

1. Include an example of my repo config with mini-dinstall, .dput.cf, .sbuildrc
