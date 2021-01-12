#!/usr/bin/env python3
#
#  __init__.py
"""
Extensions to the Dulwich Git library.
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
#  format_commit, get_untracked_paths, get_tree_changes, clone and status
#  based on https://github.com/dulwich/dulwich
#  Copyright (C) 2013 Jelmer Vernooij <jelmer@jelmer.uk>
#  |  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  |  not use this file except in compliance with the License. You may obtain
#  |  a copy of the License at
#  |
#  |      http://www.apache.org/licenses/LICENSE-2.0
#  |
#  |  Unless required by applicable law or agreed to in writing, software
#  |  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  |  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  |  License for the specific language governing permissions and limitations
#  |  under the License.
#

# stdlib
import os
import shutil
from contextlib import closing, contextmanager
from itertools import chain
from operator import itemgetter
from typing import (
		IO,
		ContextManager,
		Dict,
		Iterator,
		List,
		NamedTuple,
		Optional,
		Sequence,
		Tuple,
		TypeVar,
		Union,
		overload
		)

# 3rd party
import dulwich.repo
from click import echo
from consolekit.terminal_colours import Fore
from domdf_python_tools.compat import nullcontext
from domdf_python_tools.paths import PathPlus, maybe_make
from domdf_python_tools.typing import PathLike
from dulwich.config import StackedConfig
from dulwich.ignore import IgnoreFilterManager
from dulwich.index import Index, get_unstaged_changes
from dulwich.objects import Commit, ShaFile, Tag
from dulwich.porcelain import default_bytes_err_stream, fetch, path_to_tree_path
from typing_extensions import TypedDict

# this package
from southwark.repo import Repo

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2020 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.8.0"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = [
		"get_tags",
		"check_git_status",
		"assert_clean",
		"get_untracked_paths",
		"status",
		"StagedDict",
		"GitStatus",
		"get_tree_changes",
		"clone",
		"_DR",
		"open_repo_closing",
		"windows_clone_helper",
		]

_DR = TypeVar("_DR", bound=dulwich.repo.Repo)


class StagedDict(TypedDict):
	"""
	The values are lists of filenames, relative to the repository root.

	.. versionadded:: 0.6.1
	"""

	add: List[PathPlus]
	delete: List[PathPlus]
	modify: List[PathPlus]


class GitStatus(NamedTuple):
	"""
	Represents the output of :func:`~.status`.

	.. versionadded:: 0.6.1
	"""

	#: Dict with lists of staged paths.
	staged: StagedDict

	#: List of unstaged paths.
	unstaged: List[PathPlus]

	#: List of untracked, un-ignored & non-.git paths.
	untracked: List[PathPlus]


def get_tags(repo: Union[dulwich.repo.Repo, PathLike] = '.') -> Dict[str, str]:
	"""
	Returns a mapping of commit SHAs to tags.

	:param repo:
	"""

	tags: Dict[str, str] = {}

	with open_repo_closing(repo) as r:
		raw_tags: Dict[bytes, bytes] = r.refs.as_dict(b"refs/tags")
		for tag, sha, in raw_tags.items():
			obj = r.get_object(sha)
			if isinstance(obj, Tag):
				tags[obj.object[1].decode("UTF-8")] = tag.decode("UTF-8")
			elif isinstance(obj, Commit):
				tags[sha.decode("UTF-8")] = tag.decode("UTF-8")

	return tags


def assert_clean(repo: PathPlus, allow_config: Sequence[PathLike] = ()) -> bool:
	"""
	Returns :py:obj:`True` if the working directory is clean.

	If not, returns :py:obj:`False` and prints a helpful error message to stderr.

	:param repo:
	:param allow_config:
	"""

	allow_config = [PathPlus(filename) for filename in allow_config]

	stat = status(repo)

	modified_files = chain.from_iterable([
			stat.staged["add"],
			stat.staged["delete"],
			stat.staged["modify"],
			stat.unstaged,
			])

	if modified_files:
		for filename in modified_files:
			if filename not in allow_config:
				break
		else:
			return True

	# If we get to here the directory isn't clean
	echo(Fore.RED("Git working directory is not clean:"), err=True)

	for line in format_git_status(stat):
		echo(Fore.RED(f"  {line}"), err=True)

	return False


status_codes: Dict[str, str] = {
		"add": 'A',
		"delete": 'D',
		"modify": 'M',
		}


def check_git_status(repo_path: PathLike) -> Tuple[bool, List[str]]:
	"""
	Check the ``git`` status of the given repository.

	:param repo_path: Path to the repository root.

	:return: Whether the git working directory is clean, and the list of uncommitted files if it isn't.
	"""

	str_lines = list(format_git_status(status(repo_path)))

	# with in_directory(repo_path):
	#
	# 	lines = [
	# 			line.strip()
	# 			for line in subprocess.check_output(["git", "status", "--porcelain"]).splitlines()
	# 			if not line.strip().startswith(b"??")
	# 			]
	#
	# str_lines = [line.decode("UTF-8") for line in lines]
	return not bool(str_lines), str_lines


def format_git_status(status: GitStatus) -> Iterator[str]:
	"""
	Format the ``git`` status of the given repository for output to the terminal.

	:param status:

	:return: An iterator over the formatted list of uncommitted files.

	.. versionadded:: 0.6.1
	"""

	files: Dict[bytes, str] = {}

	for key, code in status_codes.items():
		for file in status.staged[key]:  # type: ignore
			if file in files:
				files[file] += code
			else:
				files[file] = code

	for file in status.unstaged:
		if file in files:
			files[file] += 'M'
		else:
			files[file] = 'M'

	for file, codes in sorted(files.items(), key=itemgetter(0)):
		longest = max(len(v) for v in files.values()) + 1

		status_code = ''.join(sorted(codes)).ljust(longest, ' ')
		yield f"{status_code}{file!s}"


status_excludes = {".git", ".tox", ".tox4", ".mypy_cache", ".pytest_cache", "venv", ".venv"}


def get_untracked_paths(path: PathLike, index: Index) -> Iterator[str]:
	"""
	Returns a list of untracked files.

	:param path: Path to walk.
	:param index: Index to check against.
	"""

	path = str(path)

	for dirpath, dirnames, filenames in os.walk(path):
		# Skip .git etc. and below.
		for exclude in status_excludes:
			if exclude in dirnames:
				dirnames.remove(exclude)
				if dirpath != path:
					continue
			if exclude in filenames:
				filenames.remove(exclude)
				if dirpath != path:
					continue

		for filename in filenames:
			filepath = os.path.join(dirpath, filename)

			_pp_filename = (PathPlus(path) / filepath)
			if _pp_filename.is_symlink() and not _pp_filename.resolve().is_relative_to(path):
				continue

			ip = path_to_tree_path(path, filepath)

			if ip not in index:
				yield os.path.relpath(filepath, path)


def get_tree_changes(repo: Union[PathLike, dulwich.repo.Repo]) -> StagedDict:
	"""
	Return add/delete/modify changes to tree by comparing the index to HEAD.

	:param repo: repo path or object.

	:returns: Dictionary containing changes for each type of change.

	.. versionadded:: 0.6.1
	"""

	with open_repo_closing(repo) as r:
		index = r.open_index()

		# Compares the Index to the HEAD & determines changes
		# Iterate through the changes and report add/delete/modify
		# TODO: call out to dulwich.diff_tree somehow.
		tracked_changes: StagedDict = {
				"add": [],
				"delete": [],
				"modify": [],
				}
		try:
			tree_id = r[b'HEAD'].tree  # type: ignore
		except KeyError:
			tree_id = None

		for change in index.changes_from_tree(r.object_store, tree_id):
			if not change[0][0]:
				tracked_changes["add"].append(PathPlus(change[0][1].decode("UTF-8")))
			elif not change[0][1]:
				tracked_changes["delete"].append(PathPlus(change[0][0].decode("UTF-8")))
			elif change[0][0] == change[0][1]:
				tracked_changes["modify"].append(PathPlus(change[0][0].decode("UTF-8")))
			else:
				raise NotImplementedError("git mv ops not yet supported")
		return tracked_changes


def status(repo: Union[dulwich.repo.Repo, PathLike] = '.') -> GitStatus:
	"""
	Returns staged, unstaged, and untracked changes relative to the HEAD.

	:param repo: Path to repository or repository object.
	"""

	with open_repo_closing(repo) as r:
		# 1. Get status of staged
		tracked_changes = get_tree_changes(r)

		# 2. Get status of unstaged
		index = r.open_index()
		normalizer = r.get_blob_normalizer()
		filter_callback = normalizer.checkin_normalize
		unstaged_changes = [
				PathPlus(p.decode("UTF-8")) for p in get_unstaged_changes(index, str(r.path), filter_callback)
				]

		# Remove ignored files
		ignore_manager = IgnoreFilterManager.from_repo(r)
		untracked_changes = [
				PathPlus(p) for p in get_untracked_paths(r.path, index) if not ignore_manager.is_ignored(p)
				]

		return GitStatus(tracked_changes, unstaged_changes, untracked_changes)


def clone(
		source: Union[str, bytes],
		target: Union[PathLike, bytes, None] = None,
		bare: bool = False,
		checkout: Optional[bool] = None,
		errstream: IO = default_bytes_err_stream,
		origin: Union[str, bytes] = "origin",
		depth: Optional[int] = None,
		**kwargs,
		) -> Repo:
	"""
	Clone a local or remote git repository.

	:param source: Path or URL for source repository.
	:param target: Path to target repository.
	:param bare: Whether to create a bare repository.
	:param checkout: Whether to check-out HEAD after cloning.
	:param errstream: Optional stream to write progress to.
	:param origin: Name of remote from the repository used to clone.
	:param depth: Depth to fetch at.

	:returns: The cloned repository.

	.. versionadded:: 0.6.1

	.. versionchanged:: 0.7.2

		* ``target`` now accepts :py:data:`domdf_python_tools.types.PathLike` objects.
		* ``origin`` now accepts :class:`str` objects.
	"""

	if checkout is None:
		checkout = (not bare)
	elif checkout and bare:
		raise TypeError("'checkout' and 'bare' are incompatible.")

	if isinstance(origin, bytes):
		origin = origin.decode("UTF-8")

	if isinstance(source, bytes):
		source = source.decode("UTF-8")

	if target is None:
		target = source.split('/')[-1]

	if isinstance(target, bytes):
		target = target.decode("UTF-8")

	maybe_make(target)

	if bare:
		r = Repo.init_bare(target)
	else:
		r = Repo.init(target)

	try:
		target_config = r.get_config()

		target_config.set(("remote", origin), "url", source.encode("UTF-8"))
		target_config.set(("remote", origin), "fetch", f"+refs/heads/*:refs/remotes/{origin}/*".encode("UTF-8"))
		target_config.write_to_path()
		fetch_result = fetch(
				r,
				origin,
				errstream=errstream,
				message=f"clone: from {source}".encode("UTF-8"),
				depth=depth,
				**kwargs,
				)

		head: Optional[ShaFile]

		try:
			head = r[fetch_result.refs[b'HEAD']]
		except KeyError:
			head = None
		else:
			r[b'HEAD'] = head.id

		if checkout and not bare and head is not None:
			errstream.write(b'Checking out ' + head.id + b'\n')
			r.reset_index(head.tree)  # type: ignore   # TODO

	except BaseException:
		shutil.rmtree(target, ignore_errors=True)
		r.close()
		raise

	return r


@overload
def open_repo_closing(path_or_repo: _DR) -> ContextManager[_DR]:
	...  # pragma: no cover


@overload
def open_repo_closing(path_or_repo: Union[str, os.PathLike]) -> ContextManager[Repo]:
	...  # pragma: no cover


def open_repo_closing(path_or_repo):
	"""
	Returns a context manager which will return :class:`dulwich.repo.Repo` objects unchanged,
	but will create a new :class:`dulwich.repo.Repo` when a filesystem path is given.

	.. versionadded:: 0.7.0

	:param path_or_repo: Either a :class:`dulwich.repo.Repo` object or the path of a repository.
	"""  # noqa: D400

	if isinstance(path_or_repo, dulwich.repo.BaseRepo):
		return nullcontext(path_or_repo)

	return closing(Repo(path_or_repo))


@contextmanager
def windows_clone_helper():
	"""
	Contextmanager to aid cloning on Windows during tests.

	.. versionadded:: 0.8.0

	.. attention:: This function is intended only for use in tests.

	Usage:

	.. code-block:: python

		with windows_clone_helper():
			repo = clone(...)

	"""

	_environ = dict(os.environ)  # or os.environ.copy()
	_default_backends = StackedConfig.default_backends

	try:
		name = "wordle_user"
		StackedConfig.default_backends = lambda *args: []  # type: ignore
		os.environ["USER"] = os.environ.get("USER", name)

		yield

	finally:
		os.environ.clear()
		os.environ.update(_environ)
		StackedConfig.default_backends = _default_backends  # type: ignore
