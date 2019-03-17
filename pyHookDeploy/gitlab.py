#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pyHookDeploy.utils import get_local_repos, log_event


def verify_request(header, payload):
	event, result_code = str(header.get("X-Gitlab-Event")).lower(), 0

	local_repos = get_local_repos() or None
	repo_name = payload["project"]["path_with_namespace"].strip().lower()

	if not local_repos or repo_name not in local_repos:
		# Invalid repository.
		result_code = 2
	else:
		repo_dict = local_repos[repo_name]

		if repo_dict["secret"] is not None:
			# Secret configured, expecting secret in header.
			if not header.get("X-Gitlab-Token"):
				# No signature header found.
				result_code = 3
			elif str(header.get("X-Gitlab-Token")) != str(repo_dict["secret"]):
				# Signature does not match.
				result_code = 3

	if result_code == 2:
		log_event(lvl="warning", origin=origin, event=event, repo=repo_name, status="rejected", reason="invalid_repository")
	elif result_code == 3:
		log_event(lvl="warning", origin=origin, event=event, repo=repo_name, status="rejected", reason="invalid_signature")
	else:
		return True
	return False


def get_repo(payload):
	if str(payload["ref"]).lower() == "refs/heads/master":
		local_repos = get_local_repos() or None
		if local_repos is not None:
			name = payload["project"]["path_with_namespace"].strip().lower()
			return local_repos[name]
	return None
