##########
Southwark
##########

.. start short_desc

**Extensions to the Dulwich Git library.**

.. end short_desc

(Dulwich is located in the `London Borough of Southwark <https://en.wikipedia.org/wiki/London_Borough_of_Southwark>`_)

Spun out from `repo_helper <https://github.com/domdfcoding/repo_helper>`_. Needs more tests.

.. start shields

.. list-table::
	:stub-columns: 1
	:widths: 10 90

	* - Docs
	  - |docs| |docs_check|
	* - Tests
	  - |actions_linux| |actions_windows| |actions_macos| |coveralls|
	* - PyPI
	  - |pypi-version| |supported-versions| |supported-implementations| |wheel|
	* - Anaconda
	  - |conda-version| |conda-platform|
	* - Activity
	  - |commits-latest| |commits-since| |maintained| |pypi-downloads|
	* - QA
	  - |codefactor| |actions_flake8| |actions_mypy|
	* - Other
	  - |license| |language| |requires|

.. |docs| image:: https://img.shields.io/readthedocs/southwark/latest?logo=read-the-docs
	:target: https://southwark.readthedocs.io/en/latest
	:alt: Documentation Build Status

.. |docs_check| image:: https://github.com/repo-helper/southwark/workflows/Docs%20Check/badge.svg
	:target: https://github.com/repo-helper/southwark/actions?query=workflow%3A%22Docs+Check%22
	:alt: Docs Check Status

.. |actions_linux| image:: https://github.com/repo-helper/southwark/workflows/Linux/badge.svg
	:target: https://github.com/repo-helper/southwark/actions?query=workflow%3A%22Linux%22
	:alt: Linux Test Status

.. |actions_windows| image:: https://github.com/repo-helper/southwark/workflows/Windows/badge.svg
	:target: https://github.com/repo-helper/southwark/actions?query=workflow%3A%22Windows%22
	:alt: Windows Test Status

.. |actions_macos| image:: https://github.com/repo-helper/southwark/workflows/macOS/badge.svg
	:target: https://github.com/repo-helper/southwark/actions?query=workflow%3A%22macOS%22
	:alt: macOS Test Status

.. |actions_flake8| image:: https://github.com/repo-helper/southwark/workflows/Flake8/badge.svg
	:target: https://github.com/repo-helper/southwark/actions?query=workflow%3A%22Flake8%22
	:alt: Flake8 Status

.. |actions_mypy| image:: https://github.com/repo-helper/southwark/workflows/mypy/badge.svg
	:target: https://github.com/repo-helper/southwark/actions?query=workflow%3A%22mypy%22
	:alt: mypy status

.. |requires| image:: https://dependency-dash.repo-helper.uk/github/repo-helper/southwark/badge.svg
	:target: https://dependency-dash.repo-helper.uk/github/repo-helper/southwark/
	:alt: Requirements Status

.. |coveralls| image:: https://img.shields.io/coveralls/github/repo-helper/southwark/master?logo=coveralls
	:target: https://coveralls.io/github/repo-helper/southwark?branch=master
	:alt: Coverage

.. |codefactor| image:: https://img.shields.io/codefactor/grade/github/repo-helper/southwark?logo=codefactor
	:target: https://www.codefactor.io/repository/github/repo-helper/southwark
	:alt: CodeFactor Grade

.. |pypi-version| image:: https://img.shields.io/pypi/v/Southwark
	:target: https://pypi.org/project/Southwark/
	:alt: PyPI - Package Version

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/Southwark?logo=python&logoColor=white
	:target: https://pypi.org/project/Southwark/
	:alt: PyPI - Supported Python Versions

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/Southwark
	:target: https://pypi.org/project/Southwark/
	:alt: PyPI - Supported Implementations

.. |wheel| image:: https://img.shields.io/pypi/wheel/Southwark
	:target: https://pypi.org/project/Southwark/
	:alt: PyPI - Wheel

.. |conda-version| image:: https://img.shields.io/conda/v/domdfcoding/Southwark?logo=anaconda
	:target: https://anaconda.org/domdfcoding/Southwark
	:alt: Conda - Package Version

.. |conda-platform| image:: https://img.shields.io/conda/pn/domdfcoding/Southwark?label=conda%7Cplatform
	:target: https://anaconda.org/domdfcoding/Southwark
	:alt: Conda - Platform

.. |license| image:: https://img.shields.io/github/license/repo-helper/southwark
	:target: https://github.com/repo-helper/southwark/blob/master/LICENSE
	:alt: License

.. |language| image:: https://img.shields.io/github/languages/top/repo-helper/southwark
	:alt: GitHub top language

.. |commits-since| image:: https://img.shields.io/github/commits-since/repo-helper/southwark/v0.9.0
	:target: https://github.com/repo-helper/southwark/pulse
	:alt: GitHub commits since tagged version

.. |commits-latest| image:: https://img.shields.io/github/last-commit/repo-helper/southwark
	:target: https://github.com/repo-helper/southwark/commit/master
	:alt: GitHub last commit

.. |maintained| image:: https://img.shields.io/maintenance/yes/2023
	:alt: Maintenance

.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/Southwark
	:target: https://pypi.org/project/Southwark/
	:alt: PyPI - Downloads

.. end shields

Installation
--------------

.. start installation

``Southwark`` can be installed from PyPI or Anaconda.

To install with ``pip``:

.. code-block:: bash

	$ python -m pip install Southwark

To install with ``conda``:

	* First add the required channels

	.. code-block:: bash

		$ conda config --add channels https://conda.anaconda.org/conda-forge
		$ conda config --add channels https://conda.anaconda.org/domdfcoding

	* Then install

	.. code-block:: bash

		$ conda install Southwark

.. end installation
