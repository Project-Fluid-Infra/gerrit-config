#
# Copyright (C) 2021 ProjectFluid
#
# SPDX-License-Identifier: Apache-2.0
#

from gerritupdate.utils.constants import GERRIT_URL_BASE
import json
import os
import requests
from urllib.parse import quote_plus

class Config:
	GERRIT_USER = os.environ.get("GERRIT_USER")
	GERRIT_PASS = os.environ.get("GERRIT_PASS")

	GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

class Gerrit:
	@staticmethod
	def get_projects(auth=None):
		url = f"{GERRIT_URL_BASE}/a/projects/?t" if auth else f"{GERRIT_URL_BASE}/projects/?t"
		resp = requests.get(url, auth=auth)
		if resp.status_code != 200:
			raise Exception(f"Error communicating with gerrit: {resp.status_code}: {resp.text}")
		projects = json.loads(resp.text[5:])
		nodes = {}

		for name, project in projects.items():
			nodes[name] = []

		for name, project in projects.items():
			parent = project.get("parent")
			if parent:
				nodes[parent].append(name)
		for project in nodes.keys():
			nodes[project] = sorted(nodes[project])
		return nodes

	@staticmethod
	def update_parent(child, parent, auth=None):
		child = quote_plus(child)
		url = f"{GERRIT_URL_BASE}/a/projects/{child}/parent" if auth else f"{GERRIT_URL_BASE}/projects/{child}/parent"
		print(f"Updating {child}'s parent to {parent}")
		resp = requests.put(url, json=({"parent": parent, "commit_message": "Auto update from gerrit_config"}), auth=auth)
		if resp.status_code != 200:
			if resp.status_code == 404:
				project_creator_url = f"{GERRIT_URL_BASE}/a/projects/{child}" if auth else f"{GERRIT_URL_BASE}/projects/{child}"
				requests.put(project_creator_url, json=({"parent": parent}), auth=auth)
			else:
				raise Exception(f"Error communicating with gerrit: {resp.status_code}: {resp.text}")
