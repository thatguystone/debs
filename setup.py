import imp
from distutils.core import setup

debs = imp.load_source('debs', 'debs')

setup(name='debs',
	version=debs.get_changelog_version('.'),
	description='Automated .deb builder',
	author='Andrew Stone',
	author_email='a@stoney.io',
	url='https://github.com/thatguystone/debs',
	scripts=['debs'],
	data_files=[
		('/usr/bin', ['debs-sign-remote']),
	],
)
