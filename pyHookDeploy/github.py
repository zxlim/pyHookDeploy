#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hmac
import requests

from hashlib import sha1
from netaddr import IPAddress, IPNetwork
from pyHookDeploy.utils import get_local_repos, log_event


def verify_event(header):
	if not header.get("X-GitHub-Event"):
		# Required header does not exist. Treat request as invalid.
		return False, "unknown"
	elif str(header.get("X-GitHub-Event")).lower() not in ["ping", "push"]:
		# Invalid or unsupported event.
		return False, str(header.get("X-GitHub-Event")).lower()
	# Supported Event.
	return True, str(header.get("X-GitHub-Event")).lower()


def verify_header(header):
	# All webhook event requests will contain "GitHub-Hookshot" in their user-agent.
	if not header.get("User-Agent") or not header.get("Content-Type"):
		# Required header does not exist. Treat request as invalid.
		return False
	elif "GitHub-Hookshot/" not in str(header.get("User-Agent")):
		# Invalid user agent.
		return False
	elif str(header.get("Content-Type")).lower() != "application/json":
		# Unsupported content type.
		return False
	return True


def verify_hmac(data, secret, signature):
	secret = bytes(str(secret), "utf-8")
	signer = hmac.new(secret, data, sha1)

	if hmac.compare_digest(str(signature), str(signer.hexdigest())):
		# Valid signature.
		return True
	# Invalid signature.
	return False


def verify_origin_ip(origin_ip_str):
	origin_ip, valid_origin_networks = None, None

	try:
		origin_ip = IPAddress(str(origin_ip_str).strip())
		valid_origin_networks = list(IPNetwork(ip) for ip in requests.get("https://api.github.com/meta").json()["hooks"])
	except:
		# Failed to obtain necessary information to validate origin. Assume invalid origin.
		return False

	for subnet in valid_origin_networks:
		if origin_ip in subnet:
			# Request came from a valid GitHub IP address block. Origin is validated.
			return True
	# Request came from an unknown IP address. Origin is invalid.
	return False


def verify_request(origin_ip, header, request):
	event, origin, r = "unknown", "github", None

	if not verify_origin_ip(origin_ip):
		log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, status="rejected", reason="origin_ip_invalid")
		return False, event, r
	elif not verify_header(header):
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
	r_name = payload["repository"]["full_name"].strip().lower()

	if local_repos is None or r_name not in local_repos:
		log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, repo=r_name, status="rejected", reason="repository_invalid")
		return False, event, r

	# Dictionary containing repository configuration extracted from "local_repos.txt".
	r = local_repos[r_name]

	if r["secret"] is not None:
		if not header.get("X-Hub-Signature"):
			# Required header does not exist. Treat request as invalid.
			log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, repo=r_name, status="rejected", reason="signature_header_invalid")
			return False, event, r

		hub_signature = header.get("X-Hub-Signature").strip().split("=")

		if hub_signature[0] != "sha1":
			# Unsupported hash algorithm. Treat request as invalid.
			log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, repo=r_name, status="rejected", reason="signature_algo_unsupported")
			return False, event, r
		elif not verify_hmac(request.data, r["secret"], hub_signature[1]):
			# Invalid signature.
			log_event(lvl="warning", origin=origin, origin_ip=origin_ip, event=event, repo=r_name, status="rejected", reason="signature_invalid")
			return False, event, r

	# Request is verified to be valid.
	if event == "push":
		# Only perform branch checking for push events.
		if payload["ref"].lower() != "refs/heads/master":
			# Event is not triggered by master branch.
			log_event(lvl="debug", origin=origin, origin_ip=origin_ip, event=event, repo=r_name, status="rejected", reason="repository_not_master")
			r = None
		else:
			# Add the hash of the latest commit.
			r["after_hash"] = payload["after"]

	return True, event, r
