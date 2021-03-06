# stdlib
import platform

# 3rd party
import pytest
from domdf_python_tools.compat import PYPY36
from pytest_regressions.file_regression import FileRegressionFixture

# this package
from southwark.log import Log

pypy_windows_dulwich = pytest.mark.skipif(
		PYPY36 and platform.system() == "Windows",
		reason=
		"Dulwich causes 'TypeError: os.scandir() doesn't support bytes path on Windows, use Unicode instead'",
		)


@pypy_windows_dulwich
def test_log(tmp_repo, file_regression: FileRegressionFixture):
	file_regression.check(Log(tmp_repo).log())


@pypy_windows_dulwich
def test_log_reverse(tmp_repo, file_regression: FileRegressionFixture):
	file_regression.check(Log(tmp_repo).log(reverse=True))


@pypy_windows_dulwich
def test_log_from_tag(tmp_repo, file_regression: FileRegressionFixture):
	file_regression.check(Log(tmp_repo).log(from_tag="v2.0.0"))

	with pytest.raises(ValueError, match="No such tag 'v5.0.0'"):
		Log(tmp_repo).log(from_tag="v5.0.0")
