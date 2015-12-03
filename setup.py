from distutils.core import setup

from debs import cfg, package

pkg = package.load('.', cfg.Cfg())

setup(name=pkg.name,
	version=pkg.version,
	description='Automated .deb builder',
	author='Andrew Stone',
	author_email='a@stoney.io',
	url='https://github.com/thatguystone/debs',
	packages=['debs'],
	scripts=['bin/debs', 'bin/debs-sign-remote'],
)
