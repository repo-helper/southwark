# stdlib
from typing import Optional

# 3rd party
import pytest
from coincidence.regressions import AdvancedFileRegressionFixture
from consolekit import click_command
from consolekit.testing import CliRunner

# this package
from southwark.click import commit_message_option, commit_option


@commit_message_option(default="Default commit message")
@commit_option(default=None)
@click_command()
def main(commit: bool, message: str) -> None:
	"""
	Some git script.
	"""

	print(commit)
	print(message)


def test_help(advanced_file_regression: AdvancedFileRegressionFixture):

	runner = CliRunner()

	result = runner.invoke(main, catch_exceptions=False, args="--help")
	assert result.exit_code == 0
	result.check_stdout(advanced_file_regression)


def test_defaults(advanced_file_regression: AdvancedFileRegressionFixture):

	runner = CliRunner()

	result = runner.invoke(main, catch_exceptions=False)
	assert result.exit_code == 0
	result.check_stdout(advanced_file_regression)


@pytest.mark.parametrize("default", [True, False, None])
def test_commit_option(advanced_file_regression: AdvancedFileRegressionFixture, default: Optional[bool]):

	@commit_option(default=default)
	@click_command()
	def main(commit: bool) -> None:
		"""
		Some git script.
		"""

		print(commit)

	runner = CliRunner()

	result = runner.invoke(main, catch_exceptions=False, args="--help")
	assert result.exit_code == 0
	result.check_stdout(advanced_file_regression)

	result = runner.invoke(main, catch_exceptions=False)
	assert result.exit_code == 0
	assert result.stdout.rstrip() == str(default)
