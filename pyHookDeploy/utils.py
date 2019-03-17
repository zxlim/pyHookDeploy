#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os

from flask import current_app as app, jsonify
from git import Repo
from logging import getLogger


def handler_badrequest(error):
	return "Bad Request", 400


def json_response(status_code=200, message="OK"):
	response = jsonify({"status_code": status_code, "message": message})
	response.status_code = status_code
	return response


def log_event(lvl="info", origin="unknown", event="none", repo="none", status="unknown", reason="none"):
	logger_webhook = getLogger("webhook")

	if lvl.lower() == "info":
		logger_webhook.info("origin={0}|event={1}|repository={2}|status={3}|reason={4}".format(origin, event, repo, status, reason))
	elif lvl.lower() == "warning":
		logger_webhook.warning("origin={0}|event={1}|repository={2}|status={3}|reason={4}".format(origin, event, repo, status, reason))
	elif lvl.lower() == "error":
		logger_webhook.error("origin={0}|event={1}|repository={2}|status={3}|reason={4}".format(origin, event, repo, status, reason))
	elif lvl.lower() == "critical":
		logger_webhook.critical("origin={0}|event={1}|repository={2}|status={3}|reason={4}".format(origin, event, repo, status, reason))
	else:
		# Treat it as debug.
		logger_webhook.debug("origin={0}|event={1}|repository={2}|status={3}|reason={4}".format(origin, event, repo, status, reason))


def get_local_repos():
	local_repos = {}
	file_path = str(app.LOCAL_REPO_FILE_PATH)

	if not file_path or not os.path.exists(file_path):
		return None

	try:
		with open(file_path, "r") as file:
			for line in file:
				if len(line.strip()) == 0:
					# Empty line.
					continue
				if line.strip().startswith("#"):
					# Ignore comment lines
					continue

				l = str(line).strip().lower().split(":")
				repo, name, path, key, secret = None, l[0].strip().lower(), l[1].strip(), l[2].strip(), None

				if len(l) == 4:
					secret = l[3].strip()

				if os.path.exists(key) and os.path.exists(path) and os.path.isdir(path):
					try:
						repo = Repo(path)
					except:
						# Path is not a valid git repository directory.
						continue

					local_repos[name] = {"repo": repo, "ssh_cmd": "ssh -i {0}".format(key), "secret": secret}
	except:
		pass
	return local_repos


def get_origin(header):
	if header.get("X-GitHub-Event"):
		return "github"
	elif header.get("X-Gitlab-Event"):
		return "gitlab"
	return False
