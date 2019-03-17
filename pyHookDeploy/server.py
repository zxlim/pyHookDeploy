#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pyHookDeploy import github
from pyHookDeploy import gitlab

from flask import abort, Blueprint, request
from pyHookDeploy.utils import json_response, get_origin, log_event


bp = Blueprint("server", __name__)


@bp.route("/", methods=["POST"])
def entrypoint():
	event, header, origin, payload, repo_dict = None, request.headers, None, None, None

	if header.get("Content-Type") != "application/json":
		# Only support json.
		log_event(lvl="warning", origin=origin, status="rejected", reason="invalid_content_type")
		abort(400)
	elif not request.json:
		# Request body is empty.
		log_event(lvl="warning", origin=origin, status="rejected", reason="empty_request_body")
		abort(400)

	origin, payload = get_origin(header), request.json

	if not origin:
		log_event(lvl="warning", status="rejected", reason="unknown_origin")
		abort(400)
	elif origin == "github":
		# GitHub.
		if not github.verify_request(request.remote_addr, header, request):
			abort(400)

		event = str(header.get("X-GitHub-Event")).lower()

		if event == "ping":
			# ping event.
			log_event(origin=origin, event=event, status="accepted")
			return json_response(message="pong")
		elif event != "push":
			log_event(lvl="warning", origin=origin, event=event, status="rejected", reason="invalid_event")
			abort(400)
		else:
			# Valid push event.
			repo_dict = github.get_repo(payload)
	elif origin == "gitlab":
		# Gitlab.
		if not gitlab.verify_request(header, payload):
			abort(400)

		event = str(header.get("X-Gitlab-Event")).lower()

		if event != "push hook":
			log_event(lvl="warning", origin=origin, event=event, status="rejected", reason="invalid_event")
			abort(400)
		else:
			# Valid push event.
			event = "push"
			repo_dict = gitlab.get_repo(payload)

	if repo_dict is None:
		log_event(lvl="debug", origin=origin, event=event, status="rejected", reason="not_master_branch")
		return json_response(message="Accepting only push events from master branch.")
	else:
		# Valid request. Prepare to pull latest changes.
		log_event(origin=origin, event=event, status="accepted")

	repo = repo_dict["repo"]

	with repo.git.custom_environment(GIT_SSH_COMMAND=repo_dict["ssh_cmd"]):
		repo.remotes.origin.pull()

	if str(repo.head.commit) == str(payload["after"]):
		# Successfully pulled latest changes from remote origin.
		log_event(origin=origin, event=event, status="deployed")
		return json_response()
	else:
		log_event(lvl="error", origin=origin, event=event, status="failed", reason="commit_sha1_invalid")
		return json_response(500, "Latest changes not applied successfully.")
