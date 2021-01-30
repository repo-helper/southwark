# stdlib
import getpass
import re
import socket
from pathlib import Path

# 3rd party
import pytest
from apeye.requests_url import RequestsURL
from domdf_python_tools.paths import PathPlus

# this package
from southwark.targit import BadArchiveError, TarGit, check_archive_paths

logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg"
python_logo = RequestsURL(logo_url).get().content


def test_targit(tmp_pathplus, monkeypatch):
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

	print(list(t.history))

	for state in t.history:
		assert state.device == socket.gethostname()
		assert state.user == getpass.getuser()
		assert len(state.id) == 40

	assert len(list(t.history)) == 4

	t.close()

	with pytest.raises(FileExistsError, match="TarGit file '.*' already exists."):
		TarGit(tmp_pathplus / "file.tar.gz", 'w')

	with pytest.raises(ValueError, match="Unknown IO mode 'wb'"):
		TarGit(tmp_pathplus / "file.tar.gz", "wb")  # type: ignore

	with pytest.raises(ValueError, match="Unknown IO mode 't'"):
		TarGit(tmp_pathplus / "file.tar.gz", 't')  # type: ignore


def test_check_archive_paths():

	class Archive:

		def getnames(self):
			return ["foo/bar/baz.py", "code.c"]

	assert check_archive_paths(Archive())  # type: ignore

	class Archive:  # type: ignore

		def getnames(self):
			return ["/usr/bin/malware.sh", "~/.local/bin/malware.sh", "./.local/bin/malware.sh"]

	with pytest.raises(
			BadArchiveError,
			match="Refusing to extract an archive containing files utilising path traversal.",
			):
		check_archive_paths(Archive())  # type: ignore
