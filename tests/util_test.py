from nose.tools import *

from debs import util

def test_perl_dict():
	pd = util.perl_dict({
		'"blah test"': 123,
	})

	assert_equal('{\n"\\"blah test\\"" => "123",\n}', pd)

	pd = util.perl_dict({})
	assert_equal('{}', pd)
