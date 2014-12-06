# debs

For building your .debs.

This is a wrapper around sbuild and dput, but it automates it all for you.

## Todo

1. Config file for specifying a build matrix with multiple remote repos and archs
	1. Support building multiple projects in different dirs
1. Support building from .dsc files
	1. Detect when debian dir present, fail accordingly
1. Include an example of my repo config with mini-dinstall, .dput.cf, .sbuildrc
1. Include release signing script
