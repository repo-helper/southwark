# 3rd party
from coincidence.selectors import not_windows
from domdf_python_tools.paths import PathPlus
from pytest_git import GitRepo  # type: ignore
from pytest_regressions.data_regression import DataRegressionFixture

# this package
from southwark import assert_clean, check_git_status, get_tags


def test_get_tags(tmp_repo, data_regression: DataRegressionFixture):
	data_regression.check(get_tags(tmp_repo))


@not_windows(reason="Patchy on Windows")
def test_check_git_status(git_repo: GitRepo):
	repo_path = PathPlus(git_repo.workspace)
	clean, files = check_git_status(repo_path)
	assert clean
	assert files == []

	(repo_path / "file.txt").write_text("Hello World")
	clean, files = check_git_status(repo_path)
	assert clean
	assert files == []

	git_repo.run("git add file.txt")
	clean, files = check_git_status(repo_path)
	assert not clean
	assert files == ["A file.txt"]

	git_repo.api.index.commit("Initial commit")
	clean, files = check_git_status(repo_path)
	assert clean
	assert files == []

	(repo_path / "file.txt").write_text("Hello Again")
	clean, files = check_git_status(repo_path)
	assert not clean
	assert files == ["M file.txt"]


def test_assert_clean(git_repo: GitRepo, capsys, monkeypatch):
	monkeypatch.setenv("GIT_COMMITTER_NAME", "Guido")
	monkeypatch.setenv("GIT_COMMITTER_EMAIL", "guido@python.org")
	monkeypatch.setenv("GIT_AUTHOR_NAME", "Guido")
	monkeypatch.setenv("GIT_AUTHOR_EMAIL", "guido@python.org")

	repo_path = PathPlus(git_repo.workspace)
	assert assert_clean(repo_path)

	(repo_path / "file.txt").write_text("Hello World")
	assert assert_clean(repo_path)

	git_repo.run("git add file.txt")
	assert not assert_clean(repo_path)
	assert capsys.readouterr().err.splitlines() == [
			"Git working directory is not clean:",
			"  A file.txt",
			]

	git_repo.api.index.commit("Initial commit")
	assert assert_clean(repo_path)

	(repo_path / "file.txt").write_text("Hello Again")
	assert not assert_clean(repo_path)
	assert capsys.readouterr().err.splitlines() == [
			"Git working directory is not clean:",
			"  M file.txt",
			]
