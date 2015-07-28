from distutils.core import setup

setup(name='debs',
	version='1.0.1',
	description='Automated .deb builder',
	author='Andrew Stone',
	author_email='a@stoney.io',
	url='https://github.com/thatguystone/debs',
	scripts=['debs'],
	data_files=[
		('/usr/bin', ['debs-sign-remote']),
	],
)
