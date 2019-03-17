#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging

from flask import Flask


def init_app():
	app = Flask(__name__)

	with app.app_context():
		app.config["DEBUG"] = False
		app.config["TESTING"] = False
		app.config["JSON_AS_ASCII"] = False
		app.LOCAL_REPO_FILE_PATH = "local_repos.txt"

		logger_werkzeug = logging.getLogger("werkzeug")
		logger_werkzeug.setLevel(logging.ERROR)

		fh = logging.FileHandler("deployment.log")
		fh.setLevel(logging.INFO)
		fh.setFormatter(logging.Formatter("[%(asctime)s - %(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))

		logger_webhook = logging.getLogger("webhook")
		logger_webhook.setLevel(logging.INFO)
		logger_webhook.addHandler(fh)

		from pyHookDeploy.server import bp
		from pyHookDeploy.utils import handler_badrequest

		app.register_blueprint(bp)
		app.register_error_handler(400, handler_badrequest)
		app.register_error_handler(405, handler_badrequest)

	return app
