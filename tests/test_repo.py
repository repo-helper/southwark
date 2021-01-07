# 3rd party
from pytest_regressions.data_regression import DataRegressionFixture

# this package
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
