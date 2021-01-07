#!/usr/bin/env python3
#
#  config.py
"""
Utilities for repository configuration.

.. versionadded:: 0.5.0
"""
#
#  Copyright © 2020 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#
#  get_user_identity and Repo based on https://github.com/dulwich/dulwich
#  Copyright (C) 2013 Jelmer Vernooij <jelmer@jelmer.uk>
#  |  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  |  not use this file except in compliance with the License. You may obtain
#  |  a copy of the License at
#  |
#  |	  http://www.apache.org/licenses/LICENSE-2.0
#  |
#  |  Unless required by applicable law or agreed to in writing, software
#  |  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  |  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  |  License for the specific language governing permissions and limitations
#  |  under the License.
#

# stdlib
from typing import Dict

# 3rd party
from dulwich.config import ConfigFile

__all__ = ["set_remote_ssh", "set_remote_http", "get_remotes"]


def set_remote_ssh(config: ConfigFile, domain: str, username: str, repo: str, name: str = "origin"):
	"""
	Set the remote url for the repository, using SSH.

	:param config:
	:param domain:
	:param username:
	:param repo:
	:param name: The name of the remote to set.

	.. versionadded:: 0.5.0
	"""

	config.set(("remote", name), "url", f"git@{domain}:{username}/{repo}.git".encode("UTF-8"))


def set_remote_http(config: ConfigFile, domain: str, username: str, repo: str, name: str = "origin"):
	"""
	Set the remote url for the repository, using HTTP.

	:param config:
	:param domain:
	:param username:
	:param repo:
	:param name: The name of the remote to set.

	.. versionadded:: 0.5.0
	"""

	config.set(("remote", name), "url", f"https://{domain}/{username}/{repo}.git".encode("UTF-8"))


set_remote_html = set_remote_http


def get_remotes(config: ConfigFile) -> Dict[str, str]:
	"""
	Returns a dictionary mapping remote names to URLs.

	:param config:

	.. versionadded:: 0.5.0
	"""

	remotes = {}

	for key in list(config.keys()):
		if key[0] == b"remote":
			url = config.get(key, "url")
			if url is not None:
				remotes[key[1].decode("UTF-8")] = url.decode("UTF-8")

	return remotes
