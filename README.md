# debs

For building your .debs.

This is a wrapper around sbuild and dput, but it automates it all for you.

## Config File

The configuration file, named `.debs`, contains default arguments to pass to `debs`. The arguments may be newline separated, if you wish. For example:

````
-d wheezy- -d -i386
-r deb-host
pkg1
pkg2
```

## Installing debs

1. Add `deb http://deb.stoney.io/ testing/` to your `sources.list`.
1. Install the archive keys: `sudo apt-get install stoney.io-archive-keyring`
1. `sudo aptitude install debs`

## Todo

1. Include an example of my repo config with mini-dinstall, .dput.cf, .sbuildrc
1. Include release signing script
