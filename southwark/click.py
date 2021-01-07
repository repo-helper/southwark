#!/usr/bin/env python3
#
#  __init__.py
"""
Extensions to `click <https://click.palletsprojects.com>`_.

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

# stdlib
from typing import Callable, Optional

# 3rd party
import click

__all__ = ["commit_option", "commit_message_option"]


def commit_option(default: Optional[bool]) -> Callable:
	"""
	Decorator to add the ``--commit / --no-commit`` option to a click command.

	.. versionadded:: 0.5.0

	:param default: Whether to commit automatically.

	* :py:obj:`None` -- Ask first
	* :py:obj:`True` -- Commit automatically
	* :py:obj:`False` -- Don't commit
	"""

	if default is True:
		default_text = "Commit automatically"
	elif default is False:
		default_text = "Don't commit"
	else:
		default_text = "Ask first"

	return click.option(
			"-y/-n",
			"--commit/--no-commit",
			default=lambda: default,
			show_default=default_text,
			help="Commit or do not commit any changed files.",
			)


def commit_message_option(default: str) -> Callable:
	"""
	Decorator to add the ``-m / --message`` option to a click command.

	.. versionadded:: 0.5.0

	:param default: The default commit message.
	"""

	return click.option(
			"-m",
			"--message",
			type=click.STRING,
			default=default,
			help="The commit message to use.",
			show_default=True,
			)
