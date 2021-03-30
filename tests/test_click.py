# 3rd party
import pytest
from consolekit import click_command
from consolekit.testing import CliRunner
from pytest_regressions.file_regression import FileRegressionFixture

# this package
from southwark.click import commit_message_option, commit_option


@commit_message_option(default="Default commit message")
@commit_option(default=None)
@click_command()
def main(commit: bool, message: str):
	"""
	Some git script.
	"""

	print(commit)
	print(message)


def test_help(file_regression: FileRegressionFixture):

	runner = CliRunner()

	result = runner.invoke(main, catch_exceptions=False, args="--help")
	assert result.exit_code == 0
	result.check_stdout(file_regression)


def test_defaults(file_regression: FileRegressionFixture):

	runner = CliRunner()

	result = runner.invoke(main, catch_exceptions=False)
	assert result.exit_code == 0
	result.check_stdout(file_regression)


@pytest.mark.parametrize("default", [True, False, None])
def test_commit_option(file_regression: FileRegressionFixture, default):

	@commit_option(default=default)
	@click_command()
	def main(commit: bool):
		"""
		Some git script.
		"""

		print(commit)

	runner = CliRunner()

	result = runner.invoke(main, catch_exceptions=False, args="--help")
	assert result.exit_code == 0
	result.check_stdout(file_regression)

	result = runner.invoke(main, catch_exceptions=False)
	assert result.exit_code == 0
	assert result.stdout.rstrip() == str(default)
