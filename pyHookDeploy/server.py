#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHookDeploy import github
from pyHookDeploy import gitlab

from flask import abort, Blueprint, request
from pyHookDeploy.utils import json_response, log_event


bp = Blueprint("server", __name__)


@bp.route("/", methods=["POST"])
def entrypoint():
	event, header, origin, origin_ip, repo_data = "unknown", request.headers, "unknown", request.remote_addr, None

	# Fix for reverse proxies.
	if header.get("X-Real-IP") is not None:
		origin_ip = header.get("X-Real-IP")
	elif header.get("X-Forwarded-For") is not None:
		origin_ip = header.get("X-Forwarded-For")
	

	if header.get("X-GitHub-Event"):
		# GitHub Webhook Event.
		origin = "github"
		check, event, repo_data = github.verify_request(origin_ip, header, request)

		if not check:
			# Invalid request.
			abort(400)
	elif header.get("X-Gitlab-Event"):
		# Gitlab Webhook Event.
		origin = "gitlab"
		check, event, repo_data = gitlab.verify_request(header, request)

		if not check:
			# Invalid request.
			abort(400)
	else:
		# Invalid or unsupported origin.
		log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, status="rejected", reason="origin_invalid")
		abort(400)

	if event == "ping":
		# Ping event.
		return json_response(message="pong")
	elif repo_data is None:
		# Push event on non-master branch.
		return json_response(message="Accepting push events triggered by master branch only.")
	else:
		# Push event.
		repo = repo_data["repo"]

		with repo.git.custom_environment(GIT_SSH_COMMAND=repo_data["ssh_cmd"]):
			repo.remotes.origin.pull()

		if str(repo.head.commit) == str(repo_data["after_hash"]):
			# Successfully pulled latest changes from remote origin.
			log_event(origin=origin, origin_ip=origin_ip, event=event, status="deployed")
			return json_response()
		else:
			log_event(lvl="error", origin=origin, origin_ip=origin_ip, event=event, status="failed", reason="commit_sha1_invalid")
			return json_response(500, "Latest changes not applied successfully.")
