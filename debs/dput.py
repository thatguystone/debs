from . import run

def match(*names):
	remotes = set()

	lines = run.get('dput', '--host-list').split('\n')
	lines = filter(None, lines)
	for h in lines:
		parts = h.split(' => ')
		if len(parts) != 2:
			continue

		name = parts[0]
		url = parts[1].split()[0]

		matches = \
			'all' in names or \
			not names or \
			name in names or \
			url in names
		if matches:
			remotes.add((name, url))

	remotes = list(remotes)
	remotes.sort()

	return remotes

def put(name, chgs):
	run.check('dput', name[0], chgs)
