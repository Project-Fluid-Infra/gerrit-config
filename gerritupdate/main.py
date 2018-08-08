#
# Copyright (C) 2021 ProjectFluid
#
# SPDX-License-Identifier: Apache-2.0
#

from gerritupdate.utils.lib import Gerrit, Config
from gerritupdate.utils.constants import GITHUB_ORG_NAME
from github import Github
import requests
import yaml

def update():
	if Config.GERRIT_USER and Config.GERRIT_PASS:
		auth = requests.auth.HTTPBasicAuth(Config.GERRIT_USER, Config.GERRIT_PASS)
	else:
		auth = None

	print("Updating gerrit permissions...")

	with open("structure.yml", "r") as f:
		desired_projects = yaml.load(f.read(), Loader=yaml.BaseLoader)

	live_projects = Gerrit.get_projects(auth)

	changes = {}

	for parent, children in desired_projects.items():
		if parent in live_projects:
			if set(live_projects[parent]) == set(desired_projects[parent]):
				continue
			else:
				changes[parent] = list(set(desired_projects[parent]) - set(live_projects[parent]))
				if not changes[parent]:
					del changes[parent]
		else:
			changes[parent] = children

	if changes:
		for parent, children in changes.items():
			for child in children:
				Gerrit.update_parent(child, parent, auth)

	print("Creating github repos...")

	g = Github(Config.GITHUB_TOKEN)

	github_projects = {x.full_name for x in g.get_organization(GITHUB_ORG_NAME).get_repos()}
	gerrit_projects = set()
	for parent, children in live_projects.items():
		if parent.startswith(f"{GITHUB_ORG_NAME}/"):
			gerrit_projects.add(parent)
		for child in children:
			if child.startswith(f"{GITHUB_ORG_NAME}/"):
				gerrit_projects.add(child)

	missing = gerrit_projects - github_projects

	for repo in missing:
		print(f"Creating {repo} on github...")
		g.get_organization(GITHUB_ORG_NAME).create_repo(repo.replace(f"{GITHUB_ORG_NAME}/",""), has_wiki=False, has_downloads=False, has_projects=False, has_issues=False, private=False)


	print("Done!")

def refresh():
	projects = Gerrit.get_projects()

	print("---")
	for node in sorted(projects.keys()):
		children = sorted(projects[node])
		if children:
			print(f"{node}:")
			for child in projects[node]:
				print(f"  - {child}")
