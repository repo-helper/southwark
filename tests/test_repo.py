# 3rd party
from coincidence.regressions import AdvancedDataRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
from southwark import clone, status, windows_clone_helper
from southwark.config import get_remotes
from southwark.repo import Repo


def test_list_remotes(tmp_pathplus, advanced_data_regression: AdvancedDataRegressionFixture) -> None:
	repo = Repo.init(tmp_pathplus)
	config = repo.get_config()

	config.set(("remote", "origin"), "url", b"https://github.com/domdfcoding/git-toggle.git")
	config.set(("remote", "upstream"), "url", b"git@github.com:repo-helper/git-toggler.git")
	config.write_to_path()

	advanced_data_regression.check(repo.list_remotes())
	advanced_data_regression.check(get_remotes(repo.get_config()))


_err_msg = "Dulwich causes 'TypeError: os.scandir() doesn't support bytes path on Windows, use Unicode instead'"


# @pytest.mark.skipif(
# 		PYPY36 and platform.system() == "Windows",
# 		reason=_err_msg,
# 		)
def test_reset_to(tmp_pathplus: PathPlus):

	with windows_clone_helper():
		repo = clone("https://github.com/domdfcoding/domdf_python_tools", target=tmp_pathplus)

	assert repo.head() != b"b2a09de2c93fd8dae057f7f8d178ed3abeca6efe"

	for entry in repo.get_walker():
		assert entry.commit.id != b"b2a09de2c93fd8dae057f7f8d178ed3abeca6efe"
		break

	repo.reset_to("b2a09de2c93fd8dae057f7f8d178ed3abeca6efe")
	assert repo.head() == b"b2a09de2c93fd8dae057f7f8d178ed3abeca6efe"

	current_status = status(repo)

	assert not current_status.staged["add"]
	assert not current_status.staged["delete"]
	assert not current_status.staged["modify"]
	assert not current_status.unstaged
	assert not current_status.untracked

	repo = Repo(tmp_pathplus)

	for entry in repo.get_walker():
		assert entry.commit.id == b"b2a09de2c93fd8dae057f7f8d178ed3abeca6efe"
		break
