"""
Unit tests for browser_use/logging_config.py

Tests addLoggingLevel and setup_logging behavior.
"""

import logging

import pytest


@pytest.mark.unit
class TestAddLoggingLevel:
	def test_duplicate_level_name_raises(self):
		from browser_use.logging_config import addLoggingLevel

		# 'WARNING' already exists in logging module
		with pytest.raises(AttributeError, match='already defined in logging module'):
			addLoggingLevel('WARNING', 99)

	def test_duplicate_method_name_raises(self):
		from browser_use.logging_config import addLoggingLevel

		# 'warning' method already exists
		with pytest.raises(AttributeError, match='already defined in logging module'):
			addLoggingLevel('NEWLEVEL_X', 99, methodName='warning')

	def test_result_level_already_registered(self):
		"""RESULT level is registered at import time; re-registering raises."""
		from browser_use.logging_config import addLoggingLevel

		with pytest.raises(AttributeError):
			addLoggingLevel('RESULT', 35)

	def test_result_level_value(self):
		"""RESULT level should be 35 after setup."""

		assert hasattr(logging, 'RESULT')
		assert logging.RESULT == 35


@pytest.mark.unit
class TestSetupLogging:
	def test_setup_logging_runs_without_error(self):
		"""setup_logging is idempotent when called multiple times."""
		from browser_use.logging_config import setup_logging

		# Should not raise even when called again
		setup_logging()
		setup_logging()

	def test_browser_use_logger_exists(self):
		"""browser_use logger is configured after setup."""
		import browser_use.logging_config  # noqa: F401

		logger = logging.getLogger('browser_use')
		assert logger is not None

	def test_result_level_log_method(self):
		"""The root logger exposes a .result() method after setup."""
		import browser_use.logging_config  # noqa: F401

		assert callable(getattr(logging, 'result', None))
