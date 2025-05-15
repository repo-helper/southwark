# 3rd party
import dulwich.repo
import pytest
from coincidence.regressions import AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
import southwark
from southwark.log import Log


def test_log(tmp_repo: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	advanced_file_regression.check(Log(tmp_repo).log())


def test_log_from_southwark_repo(tmp_repo: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	advanced_file_regression.check(Log(southwark.Repo(tmp_repo)).log())


def test_log_from_dulwich_repo(tmp_repo: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	advanced_file_regression.check(Log(dulwich.repo.Repo(tmp_repo)).log())


def test_log_reverse(tmp_repo: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	advanced_file_regression.check(Log(tmp_repo).log(reverse=True))


def test_log_from_tag(tmp_repo: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	advanced_file_regression.check(Log(tmp_repo).log(from_tag="v2.0.0"))

	with pytest.raises(ValueError, match="No such tag 'v5.0.0'"):
		Log(tmp_repo).log(from_tag="v5.0.0")
