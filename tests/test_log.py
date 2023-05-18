# stdlib
import platform

# 3rd party
import pytest
from coincidence.regressions import AdvancedFileRegressionFixture
from domdf_python_tools.compat import PYPY36
from domdf_python_tools.paths import PathPlus

# this package
from southwark.log import Log

_err_msg = "Dulwich causes 'TypeError: os.scandir() doesn't support bytes path on Windows, use Unicode instead'"
pypy_windows_dulwich = pytest.mark.skipif(
		PYPY36 and platform.system() == "Windows",
		reason=_err_msg,
		)


# @pypy_windows_dulwich
def test_log(tmp_repo: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	advanced_file_regression.check(Log(tmp_repo).log())


@pypy_windows_dulwich
def test_log_reverse(tmp_repo: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	advanced_file_regression.check(Log(tmp_repo).log(reverse=True))


@pypy_windows_dulwich
def test_log_from_tag(tmp_repo: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	advanced_file_regression.check(Log(tmp_repo).log(from_tag="v2.0.0"))

	with pytest.raises(ValueError, match="No such tag 'v5.0.0'"):
		Log(tmp_repo).log(from_tag="v5.0.0")
