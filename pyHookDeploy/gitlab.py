#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHookDeploy.utils import get_local_repos, log_event


def verify_event(header):
	if not header.get("X-Gitlab-Event"):
		# Required header does not exist. Treat request as invalid.
		return False, "unknown"
	elif str(header.get("X-Gitlab-Event")).lower() != "push hook":
		# Invalid or unsupported event.
		return False, str(header.get("X-Gitlab-Event")).lower()
	# Supported event.
	return True, "push"


def verify_header(header):
	if not header.get("Content-Type"):
		# Required header does not exist. Treat request as invalid.
		return False
	elif str(header.get("Content-Type")).lower() != "application/json":
		# Unsupported content type.
		return False
	return True


def verify_request(header, request):
	event, origin, r = "unknown", "gitlab", None

	if not verify_header(header):
		log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, status="rejected", reason="origin_header_invalid")
		return False, event, r
		
	valid_event, event = verify_event(header)

	if not valid_event:
		log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, status="rejected", reason="event_invalid")
		return False, event, r
	elif not request.json:
		log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, status="rejected", reason="request_empty")
		return False, event, r

	local_repos = get_local_repos()
	payload = request.json
	r_name = payload["project"]["path_with_namespace"].strip().lower()

	if local_repos is None or r_name not in local_repos:
		log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, repo=r_name, status="rejected", reason="repository_invalid")
		return False, event, r

	# Dictionary containing repository configuration extracted from "local_repos.txt".
	r = local_repos[r_name]

	if r["secret"] is not None:
		if not header.get("X-Gitlab-Token"):
			# Required header does not exist. Treat request as invalid.
			log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, repo=r_name, status="rejected", reason="signature_invalid_header")
			return False, event, r
		elif r["secret"] != header.get("X-Gitlab-Token").strip():
			# Invalid signature.
			log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, repo=r_name, status="rejected", reason="signature_invalid")
			return False, event, r

	# Request is verified to be valid.
	if payload["ref"].lower() != "refs/heads/master":
		# Event is not triggered by master branch.
		log_event(lvl="debug", origin=origin, origin_ip=origin_ip, event=event, repo=r_name, status="rejected", reason="repository_not_master")
		r = None
	else:
		# Add the hash of the latest commit.
		r["after_hash"] = payload["after"]

	return True, event, r
