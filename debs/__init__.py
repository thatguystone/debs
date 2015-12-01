# MODULARIZE THIS: BREAK INTO LIBRARY WITH INI CONFIG; SUPPORT DSC, QUILT, ETC; SUPPORT DIST ALIASES; SUPPORT PACKAGE-LOCAL .SBUILDRC; USE .sbuildrc:schroot_args TO CHANGE USERS; TEST SUITE THAT DISABLES APT AND STUFF VIA LOCAL SBUILDRC;

import logging

__all__ = ['Debs']

logging.basicConfig(
	level=logging.INFO,
	format='%(levelname)-.1s: %(message)s')

class Debs(object):
	pass
