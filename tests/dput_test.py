from nose.tools import *

from debs import dput

def test_match():
	remotes = dput.match('local', 'ubuntu', 'ftp.upload.debian.org')

	rs = [r[0] for r in remotes]
	assert_in('ftp-master', rs)
	assert_in('local', rs)
	assert_in('ubuntu', rs)
