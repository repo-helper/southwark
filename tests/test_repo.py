# stdlib
import os

# 3rd party
from dulwich.config import StackedConfig
from pytest_regressions.data_regression import DataRegressionFixture

# this package
from southwark import clone, status
from southwark.config import get_remotes
from southwark.repo import Repo


def test_list_remotes(tmp_pathplus, data_regression: DataRegressionFixture):
	repo = Repo.init(tmp_pathplus)
	config = repo.get_config()

	config.set(("remote", "origin"), "url", b"https://github.com/domdfcoding/git-toggle.git")
	config.set(("remote", "upstream"), "url", b"git@github.com:repo-helper/git-toggler.git")
	config.write_to_path()

	data_regression.check(repo.list_remotes())
	data_regression.check(get_remotes(repo.get_config()))


def test_reset_to(tmp_pathplus):

	_environ = dict(os.environ)  # or os.environ.copy()
	_default_backends = StackedConfig.default_backends

	try:
		name = "wordle_user"
		StackedConfig.default_backends = lambda *args: []  # type: ignore
		os.environ["USER"] = os.environ.get("USER", name)

		repo = clone("https://github.com/domdfcoding/domdf_python_tools", target=tmp_pathplus)

	finally:
		os.environ.clear()
		os.environ.update(_environ)
		StackedConfig.default_backends = _default_backends  # type: ignore

	repo.reset_to("b2a09de2c93fd8dae057f7f8d178ed3abeca6efe", verbose=True)

	current_status = status(repo)

	assert not current_status.staged["add"]
	assert not current_status.staged["delete"]
	assert not current_status.staged["modify"]
	assert not current_status.unstaged
	assert not current_status.untracked
