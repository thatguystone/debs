import glob
import os.path

def expand(path):
	ps = glob.glob(path)
	if not ps:
		ps = [path]

	return list(map(lambda p: os.path.expanduser(p), ps))

def to_set(strl):
	return set(filter(None, map(lambda s: s.strip(), strl)))

def strip_lines(str):
	return '\n'.join(map(lambda s: s.strip(), str.splitlines()))

def perl_dict(d):
	s = ''
	for k, v in d.items():
		s += '"{}" => "{}",\n'.format(
			str(k).replace('"', r'\"'),
			str(v).replace('"', r'\"'))

	if not s:
		return '{}'
	return '{\n' + s + '}'
