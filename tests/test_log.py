# 3rd party
import pytest
from pytest_regressions.file_regression import FileRegressionFixture

# this package
from southwark.log import Log


def test_log(tmp_repo, file_regression: FileRegressionFixture):
	file_regression.check(Log(tmp_repo).log())


def test_log_reverse(tmp_repo, file_regression: FileRegressionFixture):
	file_regression.check(Log(tmp_repo).log(reverse=True))


def test_log_from_tag(tmp_repo, file_regression: FileRegressionFixture):
	file_regression.check(Log(tmp_repo).log(from_tag="v2.0.0"))

	with pytest.raises(ValueError, match="No such tag 'v5.0.0'"):
		Log(tmp_repo).log(from_tag="v5.0.0")
