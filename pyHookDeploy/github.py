#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hmac
import requests

from hashlib import sha1
from netaddr import IPAddress, IPNetwork
from pyHookDeploy.utils import get_local_repos, log_event


def verify_request(origin_ip_str, header, request):
	event, result_code = str(header.get("X-GitHub-Event")).lower(), 0

	if "GitHub-Hookshot/" not in str(header.get("User-Agent")):
		result_code = 1
	else:
		try:
			origin_verified = False
			origin_ip = IPAddress(str(origin_ip_str).strip())
			valid_origin_ips = requests.get("https://api.github.com/meta").json()["hooks"]

			for ip in valid_origin_ips:
				if origin_ip in IPNetwork(ip):
					origin_verified = True
					break;

			if not origin_verified:
				result_code = 1
		except:
			result_code = 1

	if result_code == 0:
		local_repos = get_local_repos() or None
		repo_name = request.json["repository"]["full_name"].strip().lower()

		if not local_repos or repo_name not in local_repos:
			# Invalid repository.
			result_code = 2
		else:
			repo_dict = local_repos[repo_name]

			if repo_dict["secret"] is not None:
				# Secret configured, expecting signature in header.
				if not header.get("X-Hub-Signature"):
					# No signature header found.
					result_code = 3
				else:
					sign = hmac.new(bytes(repo_dict["secret"], "utf-8"), request.data, sha1)
					signature = header.get("X-Hub-Signature").split("=")[1].strip()

					if not hmac.compare_digest(str(signature), str(sign.hexdigest())):
						# Signature does not match.
						result_code = 3

	if result_code == 1:
		log_event(lvl="warning", origin=origin, event=event, status="rejected", reason="invalid_origin")
	elif result_code == 2:
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
			name = payload["repository"]["full_name"].strip().lower()
			return name, local_repos[name]
	return None, None
