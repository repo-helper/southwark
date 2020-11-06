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
#  format_commit, get_untracked_paths, get_tree_changes and status
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
from operator import itemgetter
from typing import Dict, Iterator, List, NamedTuple, Tuple, Union

# 3rd party
import click
from consolekit.terminal_colours import Fore
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from dulwich.ignore import IgnoreFilterManager
from dulwich.index import Index, get_unstaged_changes
from dulwich.objects import Commit, Tag
from dulwich.porcelain import open_repo_closing, path_to_tree_path
from dulwich.repo import Repo
from typing_extensions import TypedDict

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2020 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.4.0"
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
		]


class StagedDict(TypedDict):
	"""
	The values are lists of filenames, relative to the repository root.

	.. versionadded:: 0.4.0
	"""

	add: List[PathPlus]
	delete: List[PathPlus]
	modify: List[PathPlus]


class GitStatus(NamedTuple):
	"""
	.. versionadded:: 0.4.0
	"""

	staged: StagedDict
	unstaged: List[PathPlus]
	untracked: List[PathPlus]


def get_tags(repo: Union[Repo, PathLike] = ".") -> Dict[str, str]:
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


def assert_clean(repo: PathPlus, allow_config: bool = False) -> bool:
	"""
	Returns :py:obj:`True` if the working directory is clean.

	If not, returns :py:obj:`False` and prints a helpful error message to stderr.

	:param repo:
	:param allow_config:
	"""

	stat, lines = check_git_status(repo)

	if stat:
		return True

	else:
		# This must not be a set, as lists are unhashable.
		if allow_config and lines in (
				["M repo_helper.yml"],
				[" M repo_helper.yml"],
				["A repo_helper.yml"],
				[" A repo_helper.yml"],
				["AM repo_helper.yml"],
				["M git_helper.yml"],
				[" M git_helper.yml"],
				["A git_helper.yml"],
				[" A git_helper.yml"],
				["D git_helper.yml"],
				[" D git_helper.yml"],
				["AM git_helper.yml"],
				):
			return True

		else:
			click.echo(Fore.RED("Git working directory is not clean:"), err=True)

			for line in lines:
				click.echo(Fore.RED(f"  {line}"), err=True)

			return False


status_codes: Dict[str, str] = {
		"add": "A",
		"delete": "D",
		"modify": "M",
		}


def check_git_status(repo_path: PathLike) -> Tuple[bool, List[str]]:
	"""
	Check the ``git`` status of the given repository.

	:param repo_path: Path to the repository root.

	:return: Whether the git working directory is clean, and the list of uncommitted files if it isn't.
	"""

	stat = status(repo_path)
	files: Dict[bytes, str] = {}

	for key, code in status_codes.items():
		for file in stat.staged[key]:  # type: ignore
			if file in files:
				files[file] += code
			else:
				files[file] = code

	for file in stat.unstaged:
		if file in files:
			files[file] += "M"
		else:
			files[file] = "M"

	str_lines = []

	for file, codes in sorted(files.items(), key=itemgetter(0)):
		longest = max(len(v) for v in files.values()) + 1

		status_code = ''.join(sorted(codes)).ljust(longest, ' ')
		str_lines.append(f"{status_code}{file!s}")

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


status_excludes = {".git", ".tox", ".mypy_cache", ".pytest_cache", "venv", ".venv"}


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
			ip = path_to_tree_path(path, filepath)

			if ip not in index:
				yield os.path.relpath(filepath, path)


def get_tree_changes(repo: Union[PathLike, Repo]) -> StagedDict:
	"""
	Return add/delete/modify changes to tree by comparing index to HEAD.

	:param repo: repo path or object
	Returns: dict with lists for each type of change

	.. versionadded:: 0.4.0
	"""

	with open_repo_closing(repo) as r:
		index = r.open_index()

		# Compares the Index to the HEAD & determines changes
		# Iterate through the changes and report add/delete/modify
		# TODO: call out to dulwich.diff_tree somehow.
		tracked_changes: StagedDict = {
				'add': [],
				'delete': [],
				'modify': [],
				}
		try:
			tree_id = r[b'HEAD'].tree  # type: ignore
		except KeyError:
			tree_id = None

		for change in index.changes_from_tree(r.object_store, tree_id):
			if not change[0][0]:
				tracked_changes['add'].append(PathPlus(change[0][1].decode("UTF-8")))
			elif not change[0][1]:
				tracked_changes['delete'].append(PathPlus(change[0][0].decode("UTF-8")))
			elif change[0][0] == change[0][1]:
				tracked_changes['modify'].append(PathPlus(change[0][0].decode("UTF-8")))
			else:
				raise NotImplementedError('git mv ops not yet supported')
		return tracked_changes


def status(repo: Union[Repo, PathLike] = ".") -> GitStatus:
	"""
	Returns staged, unstaged, and untracked changes relative to the HEAD.

	:param repo: Path to repository or repository object.

	:returns: GitStatus tuple,
		staged -  dict with lists of staged paths (diff index/HEAD)
		unstaged -  list of unstaged paths (diff index/working-tree)
		untracked - list of untracked, un-ignored & non-.git paths
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
