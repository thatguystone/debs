import os.path

DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures')

def fixture(*args):
	return os.path.join(DIR, *args)
