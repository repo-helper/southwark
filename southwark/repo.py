#!/usr/bin/env python3
#
#  repo.py
"""
Modified Dulwich repository object.

.. versionadded:: 0.3.0
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
import os
from itertools import chain
from typing import Any, Dict, Iterator, Optional, Type, TypeVar, Union, cast

# 3rd party
import click
import dulwich.index
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from dulwich import repo
from dulwich.config import StackedConfig
from dulwich.objects import Commit, Tree, TreeEntry

__all__ = ["get_user_identity", "Repo", "_R"]

_R = TypeVar("_R", bound="Repo")


def get_user_identity(config: StackedConfig, kind: Optional[str] = None) -> bytes:
	"""
	Determine the identity to use for new commits.

	If kind is set, this first checks
	:envvar:`GIT_${KIND}_NAME` and :envvar:`GIT_${KIND}_EMAIL`.

	If those variables are not set, then it will fall back
	to reading the ``user.name`` and ``user.email`` settings from
	the specified configuration.

	If that also fails, then it will fall back to using
	the current users' identity as obtained from the host
	system (e.g. the gecos field, $EMAIL, $USER@$(hostname -f).

	:param config:
	:param kind: Optional kind to return identity for, usually either ``'AUTHOR'`` or ``'COMMITTER'``.

	:returns: A user identity
	"""

	user: Optional[bytes] = None
	email: Optional[bytes] = None

	if kind:
		user_uc = os.environ.get("GIT_" + kind + "_NAME")
		if user_uc is not None:
			user = user_uc.encode("UTF-8")
		email_uc = os.environ.get("GIT_" + kind + "_EMAIL")
		if email_uc is not None:
			email = email_uc.encode("UTF-8")

	if user is None:
		try:
			user = config.get(("user", ), "name")
		except KeyError:
			user = None

	if email is None:
		try:
			email = config.get(("user", ), "email")
		except KeyError:
			email = None

	if user is None or email is None:
		default_user, default_email = repo._get_default_identity()  # type: ignore

		if user is None:
			user = default_user.encode("UTF-8")
		if email is None:
			email = default_email.encode("UTF-8")

	if email.startswith(b'<') and email.endswith(b'>'):
		email = email[1:-1]

	return user + b" <" + email + b">"


class Repo(repo.Repo):
	"""
	Modified Dulwich repository object.

	A git repository backed by local disk.

	To open an existing repository, call the constructor with
	the path of the repository.

	To create a new repository, use the Repo.init class method.

	:param root:
	"""

	def do_commit(
			self,
			message: Optional[Union[str, bytes]] = None,
			committer: Optional[Union[str, bytes]] = None,
			author: Optional[Union[str, bytes]] = None,
			commit_timestamp: Optional[float] = None,
			commit_timezone: Optional[float] = None,
			author_timestamp: Optional[float] = None,
			author_timezone: Optional[float] = None,
			tree: Optional[Any] = None,
			encoding: Optional[Union[str, bytes]] = None,
			ref: bytes = b'HEAD',
			merge_heads: Optional[Any] = None
			) -> bytes:
		"""
		Create a new commit.

		If not specified, `committer` and `author` default to
		:func:`get_user_identity(..., 'COMMITTER') <.get_user_identity>`
		and :func:`get_user_identity(..., 'AUTHOR') <.get_user_identity>` respectively.

		:param message: Commit message
		:param committer: Committer fullname
		:param author: Author fullname
		:param commit_timestamp: Commit timestamp (defaults to now)
		:param commit_timezone: Commit timestamp timezone (defaults to GMT)
		:param author_timestamp: Author timestamp (defaults to commit timestamp)
		:param author_timezone: Author timestamp timezone (defaults to commit timestamp timezone)
		:param tree: SHA1 of the tree root to use (if not specified the current index will be committed).
		:param encoding: Encoding
		:param ref: Optional ref to commit to (defaults to current branch)
		:param merge_heads: Merge heads (defaults to .git/MERGE_HEADS)

		:returns: New commit SHA1
		"""

		config = self.get_config_stack()

		if committer is None:
			committer = get_user_identity(config, kind="COMMITTER")

		if author is None:
			try:
				author = get_user_identity(config, kind="AUTHOR")
			except ModuleNotFoundError as e:
				if str(e) == "No module named 'pwd'":
					author = committer
				else:
					raise

		return super().do_commit(
				message=message,
				committer=committer,
				author=author,
				commit_timestamp=commit_timestamp,
				commit_timezone=commit_timezone,
				author_timestamp=author_timestamp,
				author_timezone=author_timezone,
				tree=tree,
				encoding=encoding,
				ref=ref,
				merge_heads=merge_heads,
				)

	def _get_user_identity(
			self,
			config: "StackedConfig",
			kind: Optional[str] = None,
			) -> bytes:
		"""
		Determine the identity to use for new commits.

		:param config:
		:param kind:
		"""

		return get_user_identity(config)

	@classmethod
	def init(cls: Type[_R], path: PathLike, mkdir: bool = False) -> _R:
		"""
		Create a new repository.

		:param path: Path in which to create the repository.
		:param mkdir: Whether to create the directory if it doesn't exist.
		"""

		return super().init(path, mkdir)

	@classmethod
	def init_bare(cls: Type[_R], path: PathLike, mkdir: bool = False) -> _R:
		"""
		Create a new bare repository.

		:param path: Path in which to create the repository.
		:param mkdir:
		"""

		return super().init_bare(path, mkdir)

	def list_remotes(self) -> Dict[str, str]:
		"""
		Returns a mapping of remote names to remote URLs, for the repo's current remotes.

		.. versionadded:: 0.7.0
		"""

		remotes = {}
		config = self.get_config()

		for key in list(config.keys()):
			if key[0] == b"remote":
				remotes[key[1].decode("UTF-8")] = config.get(key, "url").decode("UTF-8")

		return remotes

	def reset_to(self, sha: Union[str, bytes]):
		"""
		Reset the state of the repository to the given commit sha.

		Any files added in subsequent commits will be removed,
		any deleted will be restored,
		and any modified will be reverted.

		.. versionadded:: 0.8.0

		:param sha:
		"""

		# this package
		from southwark import status

		if isinstance(sha, str):
			sha = sha.encode("UTF-8")

		index = self.open_index()
		directory = PathPlus(self.path)

		tree_for_sha: Tree = cast(Commit, self[sha]).tree
		tree_for_head: Tree = cast(Commit, self[b'HEAD']).tree

		dulwich.index.build_index_from_tree(
				root_path=directory,
				index_path=self.index_path(),
				object_store=self.object_store,
				tree_id=tree_for_sha,
				)

		try:
			# Based on https://github.com/dulwich/dulwich/issues/588#issuecomment-348412641
			oldtree: Tree = cast(Tree, self[tree_for_head])
			newtree: Tree = cast(Tree, self[tree_for_sha])

			contents_iterator: Iterator[TreeEntry] = self.object_store.iter_tree_contents(newtree.id)
			desired_filenames = [f.path for f in contents_iterator]

			for f in self.object_store.iter_tree_contents(oldtree.id):
				if f.path not in desired_filenames:
					# delete files that were in old branch, but not new
					(directory / f.path.decode("UTF-8")).unlink()

		except KeyError:
			click.echo("Unable to delete filed added in later commits", err=True)

		self[b'HEAD'] = sha
		index.write()

		current_status = status(self)

		for filename in chain.from_iterable([
				current_status.staged["add"],
				current_status.staged["delete"],
				current_status.staged["modify"],
				]):
			self.stage(os.path.normpath(filename.as_posix()))
