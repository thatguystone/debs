from setuptools import setup

from debs import package

pkg = package.load('.')

setup(name=pkg.name,
	version=pkg.version,
	description='Automated .deb builder',
	author='Andrew Stone',
	author_email='a@stoney.io',
	url='https://github.com/thatguystone/debs',
	packages=['debs'],
	scripts=['bin/debs'],
	data_files=[
		('/usr/bin', ['bin/debs-sign-remote'])]
	],
)
