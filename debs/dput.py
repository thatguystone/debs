from . import run

def match(*names):
	hosts = run.get('dput', '--host-list').split('\n')[1:]
	hosts = filter(None, hosts)

	remotes = set()
	for h in hosts:
		parts = h.split(' => ')
		name = parts[0]
		url = parts[1].split()[0]

		if name in names or url in names:
			remotes.add(name)

	remotes = list(remotes)
	remotes.sort()

	return remotes
