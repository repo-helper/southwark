#!/usr/bin/env python3
#
#  log.py
"""
Python implementation of ``git log``.
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
import time
from datetime import datetime
from textwrap import indent
from typing import Dict, Mapping, Optional, Union

# 3rd party
from consolekit.terminal_colours import Fore, strip_ansi
from domdf_python_tools.stringlist import DelimitedList, StringList
from domdf_python_tools.typing import PathLike
from dulwich.objects import Commit, format_timezone
from dulwich.repo import Repo

# this package
from southwark import get_tags

__all__ = ["Log"]

yellow_meta_left = Fore.YELLOW(" (")
yellow_meta_comma = Fore.YELLOW(", ")
yellow_meta_right = Fore.YELLOW(')')


class Log:
	"""
	Python implementation of ``git log``.

	:param repo: The git repository.
	"""

	#: The git repository.
	repo: Repo

	def __init__(self, repo: Union[Repo, PathLike] = '.'):
		if isinstance(repo, Repo):
			self.repo = repo
		else:
			self.repo = Repo(repo)

		#: Mapping of commit SHAs to tags.
		self.tags = get_tags(self.repo)

		#: Mapping of git refs to commit SHAs.
		self.refs: Dict[str, str] = {
				k.decode("UTF-8"): v.decode("UTF-8")
				for k,
				v in self.repo.get_refs().items()
				if not k.startswith(b"refs/tags/")
				}

		#: Mapping of local branches to the SHA of the latest commit in that branch.
		self.local_branches: Dict[str, str] = {}

		#: Mapping of remote branches to the SHA of the latest commit in that branch.
		self.remote_branches: Dict[str, str] = {}

		#: The name of the current branch
		self.current_branch: str = self.repo.refs.follow(b"HEAD")[0][1].decode("UTF-8")[11:]

		for key, value in self.refs.items():
			if key.startswith("refs/heads/"):
				self.local_branches[key[11:]] = value
			elif key.startswith("refs/remotes/"):
				self.remote_branches[key[13:]] = value

	# Based on https://www.dulwich.io/code/dulwich/blob/master/dulwich/porcelain.py
	def format_commit(self, commit: Commit) -> StringList:
		"""
		Return a human-readable commit log entry.

		:param commit: A `Commit` object
		"""

		buf = StringList()
		meta = []
		commit_id = commit.id.decode("UTF-8")

		if "HEAD" in self.refs and self.refs["HEAD"] == commit_id:
			for branch, sha in self.local_branches.items():
				if sha == commit_id and branch == self.current_branch:
					meta.append(Fore.BLUE("HEAD -> ") + Fore.GREEN(branch))
					break

		if commit_id in self.tags:
			meta.append(Fore.YELLOW(f"tag: {self.tags[commit_id]}"))

		for branch, sha in self.remote_branches.items():
			if sha == commit_id:
				meta.append(Fore.RED(branch))
				break

		if "HEAD" in self.refs and self.refs["HEAD"] == commit_id:
			for branch, sha in self.local_branches.items():
				if sha == commit_id and branch != self.current_branch:
					meta.append(Fore.GREEN(branch))
					break

		if meta:
			meta_string = yellow_meta_left + yellow_meta_comma.join(meta) + yellow_meta_right
		else:
			meta_string = ''

		buf.append(Fore.YELLOW("commit: " + commit.id.decode("UTF-8") + meta_string))

		if len(commit.parents) > 1:
			parents = DelimitedList(c.decode("UTF-8") for c in commit.parents[1:])
			buf.append(f"merge: {parents:...}")

		buf.append("Author: " + commit.author.decode("UTF-8"))

		if commit.author != commit.committer:
			buf.append("Committer: " + commit.committer.decode("UTF-8"))

		time_tuple = time.gmtime(commit.author_time + commit.author_timezone)
		time_str = time.strftime("%a %b %d %Y %H:%M:%S", time_tuple)
		timezone_str = format_timezone(commit.author_timezone).decode("UTF-8")
		buf.append(f"Date:   {time_str} {timezone_str}")

		buf.blankline()
		buf.append(indent(commit.message.decode("UTF-8"), "    "))
		buf.blankline(ensure_single=True)

		return buf

	def log(
			self,
			max_entries: Optional[int] = None,
			reverse: bool = False,
			from_date: Optional[datetime] = None,
			from_tag: Optional[str] = None,
			colour: bool = True
			) -> str:
		"""
		Return the formatted commit log.

		:param max_entries: Maximum number of entries to display
		:default max_entries: all entries
		:param reverse: Print entries in reverse order.
		:param from_date: Show commits after the given date.
		:param from_tag: Show commits after the given tag.
		:param colour: Show coloured output.
		"""

		kwargs: Mapping[str, Union[None, int, bool]] = dict(max_entries=max_entries, reverse=reverse)

		if from_date is not None and from_tag is not None:
			raise ValueError("'from_date' and 'from_tag' are exclusive.")
		elif from_date:
			kwargs["since"] = from_date.timestamp()  # type: ignore
		elif from_tag and not any(from_tag == tag for tag in self.tags.values()):
			raise ValueError(f"No such tag {from_tag!r}")

		buf = StringList()
		walker = self.repo.get_walker(**kwargs)

		for entry in walker:
			buf.append(str(self.format_commit(entry.commit)))

			if from_tag:
				commit_id = entry.commit.id.decode("UTF-8")
				if commit_id in self.tags and self.tags[commit_id] == from_tag:
					if reverse:
						buf = StringList([str(self.format_commit(entry.commit))])
					else:
						break

		if colour:
			return str(buf)
		else:
			return strip_ansi(str(buf))
