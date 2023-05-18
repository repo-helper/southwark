# stdlib
import pathlib
import shutil

# 3rd party
import pytest
from domdf_python_tools.paths import PathPlus

pytest_plugins = ("coincidence", )


@pytest.fixture()
def tmp_repo(tmp_pathplus: PathPlus) -> PathPlus:
	# TODO: integrity check of archive
	shutil.unpack_archive(str(pathlib.Path(__file__).parent / "test_log_git.zip"), str(tmp_pathplus))
	return tmp_pathplus
