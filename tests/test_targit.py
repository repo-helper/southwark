# stdlib
import getpass
import os
import re
import socket
import time
from pathlib import Path
from typing import List

# 3rd party
import pytest
from apeye.requests_url import RequestsURL
from domdf_python_tools.paths import PathPlus

# this package
from southwark.targit import BadArchiveError, SaveState, TarGit, check_archive_paths

logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg"
python_logo = RequestsURL(logo_url).get().content


def test_targit(tmp_pathplus: PathPlus, monkeypatch) -> None:
	monkeypatch.setattr(socket, "gethostname", lambda *args: "southwark.local")
	monkeypatch.setattr(getpass, "getuser", lambda *args: "user")

	t = TarGit(tmp_pathplus / "file.tar.gz", 'w')
	assert (tmp_pathplus / "file.tar.gz.lock").is_file()
	assert t.mode == 'w'

	assert isinstance(t / "foo.txt", Path)
	assert isinstance(t / "foo.txt", PathPlus)
	(t / "foo.txt").write_clean("Hello\nWorld")
	assert (t / "foo.txt").exists()

	assert t.status() == {"add": [PathPlus("foo.txt")], "delete": [], "modify": []}

	assert t.save()
	assert t.status() == {"add": [], "delete": [], "modify": []}

	(t / "logo.svg").write_bytes(python_logo)
	assert t.status() == {"add": [PathPlus("logo.svg")], "delete": [], "modify": []}

	assert t.save()
	assert t.status() == {"add": [], "delete": [], "modify": []}

	t.close()

	t = TarGit(tmp_pathplus / "file.tar.gz", 'a')
	assert t.status() == {"add": [], "delete": [], "modify": []}
	assert t.mode == 'a'

	(t / "foo.txt").write_clean("Hello\nEveryone")
	assert t.status() == {"add": [], "delete": [], "modify": [PathPlus("foo.txt")]}

	assert t.save()
	assert t.status() == {"add": [], "delete": [], "modify": []}
	assert not t.save()

	assert str(t).endswith("file.tar.gz")
	assert re.match(r"TarGit\(.*file\.tar\.gz\)", repr(t))

	history = list(t.history)

	assert len(history[0].id) == 40
	assert time.time() - history[0].time <= 1000
	assert isinstance(history[0].format_time(), str)

	for state in t.history:
		assert state.device == socket.gethostname()
		assert state.user == getpass.getuser()
		assert len(state.id) == 40

	assert len(list(t.history)) == 4

	assert (tmp_pathplus / "file.tar.gz").exists()
	assert (tmp_pathplus / "file.tar.gz").is_file()
	assert os.fspath(t) == os.path.join(os.fspath(tmp_pathplus), "file.tar.gz")

	t.close()

	with pytest.raises(FileExistsError, match="TarGit file '.*' already exists."):
		TarGit(tmp_pathplus / "file.tar.gz", 'w')

	with pytest.raises(ValueError, match="Unknown IO mode 'wb'"):
		TarGit(tmp_pathplus / "file.tar.gz", "wb")  # type: ignore

	with pytest.raises(ValueError, match="Unknown IO mode 't'"):
		TarGit(tmp_pathplus / "file.tar.gz", 't')  # type: ignore


def test_check_archive_paths():

	class Archive:

		def getnames(self) -> List[str]:
			return ["foo/bar/baz.py", "code.c"]

	assert check_archive_paths(Archive())  # type: ignore

	class Archive:  # type: ignore

		def getnames(self) -> List[str]:
			return ["/usr/bin/malware.sh", "~/.local/bin/malware.sh", "./.local/bin/malware.sh"]

	with pytest.raises(
			BadArchiveError,
			match="Refusing to extract an archive containing files utilising path traversal.",
			):
		check_archive_paths(Archive())  # type: ignore


def test_savestate():
	ss = SaveState(
			id="5087afd6fb5c031505f28510de9662c333307254",
			user="user",
			device="southwark.local",
			time=1747321683,
			timezone=3600,
			)
	assert ss.id == "5087afd6fb5c031505f28510de9662c333307254"
	assert ss.user == "user"
	assert ss.device == "southwark.local"
	assert ss.time == 1747321683
	assert ss.timezone == 3600
	assert ss.format_time() == "Thu May 15 2025 16:08:03 +0100"


def test_targit_no_file(tmp_pathplus: PathPlus):
	with pytest.raises(FileNotFoundError, match="No such TarGit file"):
		TarGit(tmp_pathplus / "asdf.tar.gz", mode='r')

	with pytest.raises(FileNotFoundError, match="No such TarGit file"):
		TarGit(tmp_pathplus / "asdf.tar.gz", mode='a')


def test_save_after_closed(tmp_pathplus: PathPlus, monkeypatch) -> None:
	monkeypatch.setattr(socket, "gethostname", lambda *args: "southwark.local")
	monkeypatch.setattr(getpass, "getuser", lambda *args: "user")

	t = TarGit(tmp_pathplus / "file.tar.gz", 'w')

	(t / "foo.txt").write_clean("Hello\nWorld")
	assert (t / "foo.txt").exists()

	assert t.status() == {"add": [PathPlus("foo.txt")], "delete": [], "modify": []}
	t.close()

	with pytest.raises(OSError, match="IO operation on closed TarGit file."):
		t.save()

	# Shouldn't have been created if not saved
	assert not (tmp_pathplus / "file.tar.gz").exists()


def test_save_opened_ro(tmp_pathplus: PathPlus, monkeypatch) -> None:
	monkeypatch.setattr(socket, "gethostname", lambda *args: "southwark.local")
	monkeypatch.setattr(getpass, "getuser", lambda *args: "user")

	t = TarGit(tmp_pathplus / "file.tar.gz", 'w')

	(t / "foo.txt").write_clean("Hello\nWorld")
	t.save()
	t.close()

	t2 = TarGit(tmp_pathplus / "file.tar.gz", 'r')
	with pytest.raises(OSError, match="Cannot write to TarGit file opened in read-only mode."):
		t2.save()


def test_history_after_closed(tmp_pathplus: PathPlus, monkeypatch) -> None:
	monkeypatch.setattr(socket, "gethostname", lambda *args: "southwark.local")
	monkeypatch.setattr(getpass, "getuser", lambda *args: "user")

	t = TarGit(tmp_pathplus / "file.tar.gz", 'w')

	(t / "foo.txt").write_clean("Hello\nWorld")
	assert (t / "foo.txt").exists()

	assert t.status() == {"add": [PathPlus("foo.txt")], "delete": [], "modify": []}
	t.save()
	t.close()

	with pytest.raises(OSError, match="IO operation on closed TarGit file."):
		list(t.history)


def test_status_after_closed(tmp_pathplus: PathPlus, monkeypatch) -> None:
	monkeypatch.setattr(socket, "gethostname", lambda *args: "southwark.local")
	monkeypatch.setattr(getpass, "getuser", lambda *args: "user")

	t = TarGit(tmp_pathplus / "file.tar.gz", 'w')

	(t / "foo.txt").write_clean("Hello\nWorld")
	assert (t / "foo.txt").exists()

	assert t.status() == {"add": [PathPlus("foo.txt")], "delete": [], "modify": []}
	t.save()
	t.close()

	with pytest.raises(OSError, match="IO operation on closed TarGit file."):
		t.status()


def test_status_readonly(tmp_pathplus: PathPlus, monkeypatch) -> None:
	monkeypatch.setattr(socket, "gethostname", lambda *args: "southwark.local")
	monkeypatch.setattr(getpass, "getuser", lambda *args: "user")

	with TarGit(tmp_pathplus / "file.tar.gz", 'w') as t:
		(t / "foo.txt").write_clean("Hello\nWorld")
		t.save()

	with TarGit(tmp_pathplus / "file.tar.gz", 'r') as t:
		assert t.status() == {"add": [], "delete": [], "modify": []}


def test_contextmanager(tmp_pathplus: PathPlus, monkeypatch) -> None:
	monkeypatch.setattr(socket, "gethostname", lambda *args: "southwark.local")
	monkeypatch.setattr(getpass, "getuser", lambda *args: "user")

	with TarGit(tmp_pathplus / "file.tar.gz", 'w') as t:

		(t / "foo.txt").write_clean("Hello\nWorld")
		assert (t / "foo.txt").exists()

		assert t.status() == {"add": [PathPlus("foo.txt")], "delete": [], "modify": []}
		t.save()

	assert t.closed
	assert (tmp_pathplus / "file.tar.gz").exists()
