#!/usr/bin/env python3
#
#  targit.py
"""
Archive where the changes to the contents are recorded using `git <https://git-scm.com/>`_.
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
import atexit
import datetime
import getpass
import os
import re
import socket
import tarfile
import time
from tempfile import TemporaryDirectory
from typing import Iterator, List, NamedTuple, Optional

# 3rd party
from domdf_python_tools.doctools import prettify_docstrings
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from dulwich.objects import format_timezone
from dulwich.repo import Repo
from filelock import FileLock, Timeout
from typing_extensions import Literal

# this package
from southwark import StagedDict, status

__all__ = [
		"Modes",
		"Status",
		"SaveState",
		"check_archive_paths",
		"BadArchiveError",
		"TarGit",
		]

Modes = Literal["r", "w", "a"]
"""
Valid modes for opening :class:`~.TarGit` archives in

* ``'r'`` -- Read only access. The archive must exist.
* ``'w'`` -- Read and write access. The archive must not exist.
* ``'a'`` -- Read and write access to an existing archive.
"""

Status = StagedDict
"""
Represents the dictionary returned by :meth:`TarGit.status() <.TarGit.status>`.

The values are lists of filenames, relative to the TarGit root.
"""


@prettify_docstrings
class SaveState(NamedTuple):
	"""
	Represents a save event in a :class:`~.TarGit` archive's history.
	"""

	# TODO: changed files

	#: The SHA id of the underlying commit.
	id: str  # noqa: A003  # pylint: disable=redefined-builtin

	#: The name of the user who made the changes.
	user: str

	#: The hostname of the device the changes were made on.
	device: str

	#: The time the changes were saved, in seconds from epoch.
	time: float

	#: The timezone the changes were made in, as a GMT offset in seconds.
	timezone: int

	def format_time(self) -> str:
		"""
		Format the save state's time in the following format::

			Thu Oct 29 2020 15:53:52 +0000

		where ``+0000`` represents GMT.
		"""  # noqa: D400

		time_tuple = time.gmtime(self.time + self.timezone)
		time_str = time.strftime("%a %b %d %Y %H:%M:%S", time_tuple)
		timezone_str = format_timezone(self.timezone).decode("UTF-8")
		return f"{time_str} {timezone_str}"


def check_archive_paths(archive: tarfile.TarFile) -> bool:
	"""
	Checks the contents of an archive to ensure it does not contain
	any filenames with absolute paths or path traversal.

	For example, the following paths would raise an :exc:`~.BadArchiveError`:

	* ``/usr/bin/malware.sh`` -- this is an absolute path.
	* ``~/.local/bin/malware.sh`` -- this tries to put the file in the user's home directory.
	* ``../.local/bin/malware.sh`` -- this uses path traversal to try to get to a parent directory.

	.. seealso:: The warning for :meth:`tarfile.TarFile.extractall` in the Python documentation.

	:param archive:
	"""  # noqa: D400

	for member_name in archive.getnames():
		member_name_p = PathPlus(member_name)
		if member_name_p.is_absolute() or ".." in member_name_p.parts or member_name.startswith('~'):
			raise BadArchiveError

	return True


class BadArchiveError(IOError):
	"""
	Exception to indicate an archive contains files utilising path traversal.
	"""

	def __init__(self):
		super().__init__("Refusing to extract an archive containing files utilising path traversal.")


class TarGit(os.PathLike):
	"""
	A "TarGit" (pronounced "target", /tɑːɡɪt/) is a ``tar.gz`` archive where the changes to the contents are
	recorded using `git <https://git-scm.com/>`_.

	:param filename: The filename of the archive.
	:param mode: The mode to open the file in.

	:raises FileNotFoundError: If the file is opened in read or append mode, but it does not exist.
	:raises FileExistsError: If the file is opened in write mode, but it already exists.
	:raises ValueError: If an unknown value for ``mode`` is given.
	"""  # noqa: D400

	__mode: Modes
	__repo: Repo
	__lock: Optional[FileLock]

	def __init__(self, filename: PathLike, mode: Modes = 'r'):
		self.filename = PathPlus(filename)
		self.__closed: bool = True

		self.__tmpdir: TemporaryDirectory = TemporaryDirectory()
		self.__tmpdir_p = PathPlus(self.__tmpdir.name)
		atexit.register(self.__exit_handler)

		if mode in {'w', 'a'}:
			lock_file = str(self.filename.with_suffix(self.filename.suffix + ".lock"))
			self.__lock = FileLock(lock_file, timeout=1)
			try:
				self.__lock.acquire()
			except Timeout:
				raise OSError(f"Unable to acquire a lock for the file '{self.filename!s}'")
		else:
			self.__lock = None

		if mode in {'r', 'a'}:
			if not self.exists():
				raise FileNotFoundError(f"No such TarGit file '{self.filename!s}'")

			with tarfile.open(
					self.filename,
					mode="r:gz",
					format=tarfile.PAX_FORMAT,
					) as tf:
				check_archive_paths(tf)
				tf.extractall(path=self.__tmpdir_p)

			self.__repo = Repo(self.__tmpdir_p)
			self.__mode = mode
			self.__closed = False

		elif mode in {'w'}:
			if self.exists():
				raise FileExistsError(f"TarGit file '{self.filename!s}' already exists.")

			# Initialise git repo in tmpdir
			self.__repo = Repo.init(self.__tmpdir_p)
			self.__mode = mode
			self.__closed = False
			self.__do_commit(message="Empty initial commit.")

		else:
			raise ValueError(f"Unknown IO mode {mode!r}")

	def save(self) -> bool:
		"""
		Saves the contents of the archive.

		Does nothing if there are no changes to be saved.

		:returns: Whether there were any changes to save.

		:raises IOError: If the file is closed, or if it was opened in read-only mode.
		"""

		if self.closed:
			raise OSError("IO operation on closed TarGit file.")
		elif self.__mode not in {'w', 'a'}:
			raise OSError("Cannot write to TarGit file opened in read-only mode.")

		current_status = self.status()

		if any([
				current_status["add"] != [],
				current_status["delete"] != [],
				current_status["modify"] != [],
				]):
			# There are changes to commit
			message = "; ".join([
					f"{len(current_status['add'])} added",
					f"{len(current_status['delete'])} deleted",
					f"{len(current_status['modify'])} modified",
					])

			self.__do_commit(message)

			with self.filename.open("wb", buffering=False) as fp:
				with tarfile.open(
						self.filename,
						mode="w:gz",
						format=tarfile.PAX_FORMAT,
						fileobj=fp,
						) as tf:
					tf.add(str(self.__tmpdir_p), arcname='')

				fp.flush()

			return True
		return False

	def status(self) -> StagedDict:
		"""
		Returns the status of the TarGit archive.

		The values in the dictionary are lists of filenames, relative to the TarGit root.

		:raises IOError: If the file is closed.
		"""

		if self.closed:
			raise OSError("IO operation on closed TarGit file.")
		elif self.__mode not in {'w', 'a'}:
			return {"add": [], "delete": [], "modify": []}

		current_status = status(self.__tmpdir_p)

		for file in (*current_status.unstaged, *current_status.untracked):
			self.__repo.stage(str(file))

		return status(self.__tmpdir_p).staged

	def __do_commit(self, message: str):
		if self.closed:
			raise OSError("IO operation on closed TarGit file.")
		elif self.__mode not in {'w', 'a'}:
			raise OSError("Cannot write to TarGit file opened in read-only mode.")

		login = getpass.getuser()
		username = f"{login} <{login}@{socket.gethostname()}>"
		current_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
		current_timezone = current_time.tzinfo.utcoffset(None).total_seconds()  # type: ignore

		self.__repo.do_commit(
				message=message.encode("UTF-8"),
				committer=username.encode("UTF-8"),
				author=username.encode("UTF-8"),
				commit_timestamp=current_time.timestamp(),
				commit_timezone=current_timezone,
				)

	def exists(self) -> bool:
		"""
		Returns whether the :class:`~.TarGit` archive exists.
		"""

		return self.filename.is_file()

	def close(self):
		"""
		Closes the :class:`~.TarGit` archive.
		"""

		self.__exit_handler()
		atexit.unregister(self.__exit_handler)

	def __exit_handler(self):
		if self.__tmpdir is not None:
			self.__tmpdir.cleanup()
		if self.__lock is not None:
			self.__lock.release()
		self.__closed = True

	@property
	def closed(self) -> bool:
		"""
		Returns whether the :class:`~.TarGit` archive is closed.
		"""

		return self.__closed

	@property
	def mode(self) -> Modes:
		"""
		Returns the mode the :class:`~.TarGit` archive was opened in.

		This defaults to ``'r'``. After the archive is closed this will show the
		last mode until the archive is opened again.
		"""

		return self.__mode

	def __truediv__(self, filename):
		"""
		Returns a :class:`~domdf_python_tools.paths.PathPlus` object
		representing the given filename relative to the archive root.

		:param filename:
		"""  # noqa: D400

		return self.__tmpdir_p / filename

	def __del__(self):
		self.close()

	def __repr__(self) -> str:
		"""
		Returns a string representation of the :class:`~.TarGit`.
		"""

		return f"{self.__class__.__name__}({self.filename})"

	def __fspath__(self) -> str:
		"""
		Returns the filename of the :class:`~.TarGit` archive.
		"""

		return os.fspath(self.filename)

	def __str__(self) -> str:
		"""
		Returns the filename of the :class:`~.TarGit` archive.
		"""

		return self.filename.as_posix()

	@property
	def history(self) -> Iterator[SaveState]:
		"""
		Returns an iterable over the historic save states of the :class:`~.TarGit`.
		:return:
		"""
		if self.closed:
			raise OSError("IO operation on closed TarGit file.")

		for entry in self.__repo.get_walker():
			# TODO: changed files

			author_m = re.match(r".*?\s+<(.*?)@(.*?)>", entry.commit.author.decode("UTF-8"))
			if author_m:
				user, device = author_m.groups()
			else:
				user, device = '', ''

			yield SaveState(
					id=entry.commit.id.decode("UTF-8"),
					user=user,
					device=device,
					time=entry.commit.author_time,
					timezone=entry.commit.author_timezone,
					)
