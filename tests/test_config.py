# 3rd party
from coincidence.regressions import AdvancedDataRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
from southwark.config import get_remotes, set_remote_http, set_remote_ssh
from southwark.repo import Repo


def test_set_remote_ssh(tmp_pathplus: PathPlus, advanced_data_regression: AdvancedDataRegressionFixture):
	repo = Repo.init(tmp_pathplus)
	config = repo.get_config()

	config.set(("remote", "upstream"), "url", b"git@github.com:repo-helper/git-toggler.git")
	set_remote_ssh(
			config,
			"github.com",
			"domdfcoding",
			"southwark",
			)

	config.write_to_path()

	advanced_data_regression.check(repo.list_remotes())
	advanced_data_regression.check(get_remotes(repo.get_config()))


def test_set_remote_http(tmp_pathplus: PathPlus, advanced_data_regression: AdvancedDataRegressionFixture):
	repo = Repo.init(tmp_pathplus)
	config = repo.get_config()

	config.set(("remote", "upstream"), "url", b"git@github.com:repo-helper/git-toggler.git")
	set_remote_http(
			config,
			"github.com",
			"domdfcoding",
			"southwark",
			)

	config.write_to_path()

	advanced_data_regression.check(repo.list_remotes())
	advanced_data_regression.check(get_remotes(repo.get_config()))
