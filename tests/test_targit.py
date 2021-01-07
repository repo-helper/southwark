# stdlib
import getpass
import os
import re
import socket
from pathlib import Path

# 3rd party
from apeye.requests_url import RequestsURL
from domdf_python_tools.paths import PathPlus

# this package
from southwark.targit import TarGit

logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg"
python_logo = RequestsURL(logo_url).get().content


def test_targit(tmp_pathplus, monkeypatch):
	monkeypatch.setattr(socket, "gethostname", lambda *args: "southwark.local")
	monkeypatch.setattr(getpass, "getuser", lambda *args: "user")

	t = TarGit(tmp_pathplus / "file.tar.gz", 'w')
	assert (tmp_pathplus / "file.tar.gz.lock").is_file()

	assert isinstance(t / "foo.txt", Path)
	assert isinstance(t / "foo.txt", PathPlus)
	(t / "foo.txt").write_clean("Hello\nWorld")
	assert (t / "foo.txt").exists()

	assert t.status() == {"add": [PathPlus("foo.txt")], "delete": [], "modify": []}

	t.save()
	assert t.status() == {"add": [], "delete": [], "modify": []}

	(t / "logo.svg").write_bytes(python_logo)
	assert t.status() == {"add": [PathPlus("logo.svg")], "delete": [], "modify": []}

	t.save()
	assert t.status() == {"add": [], "delete": [], "modify": []}

	t.close()

	t = TarGit(tmp_pathplus / "file.tar.gz", 'a')
	assert t.status() == {"add": [], "delete": [], "modify": []}

	(t / "foo.txt").write_clean("Hello\nEveryone")
	assert t.status() == {"add": [], "delete": [], "modify": [PathPlus("foo.txt")]}

	t.save()
	assert t.status() == {"add": [], "delete": [], "modify": []}

	assert str(t).endswith("file.tar.gz")
	assert re.match(r"TarGit\(.*file\.tar\.gz\)", repr(t))

	print(list(t.history))

	for state in t.history:
		assert state.device == socket.gethostname()
		assert state.user == getpass.getuser()
		assert len(state.id) == 40

	assert len(list(t.history)) == 4

	t.close()
