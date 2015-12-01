from nose.tools import *

from debs import dput

def test_match():
	remotes = dput.match('local', 'ubuntu', 'ftp.upload.debian.org')

	assert_in('ftp-master', remotes)
	assert_in('local', remotes)
	assert_in('ubuntu', remotes)
