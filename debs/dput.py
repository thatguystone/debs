from . import run

def match(*names):
	hosts = run.get('dput', '--host-list').split('\n')[1:]
	hosts = filter(None, hosts)

	remotes = set()
	for h in hosts:
		parts = h.split(' => ')
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
	print(name, chgs)
	raise Exception('implement me')
