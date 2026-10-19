"""
Simple sanity tests to verify test infrastructure is working.
"""

import pytest


@pytest.mark.unit
class TestSanity:
	"""Sanity tests for test infrastructure."""

	def test_basic_assertion(self):
		"""Test: Basic assertion works."""
		assert True

	def test_arithmetic(self):
		"""Test: Basic arithmetic."""
		assert 1 + 1 == 2

	def test_string_operations(self):
		"""Test: String operations work."""
		assert 'hello'.upper() == 'HELLO'

	@pytest.mark.asyncio
	async def test_async_function(self):
		"""Test: Async functions work in pytest."""
		import asyncio

		await asyncio.sleep(0.001)
		assert True
