"""
Unit tests for browser_use/telemetry/views.py and service.py

Tests telemetry event models and the ProductTelemetry service behavior.
"""

import pytest

from browser_use.telemetry.views import (
	AgentEndTelemetryEvent,
	AgentRunTelemetryEvent,
	AgentStepTelemetryEvent,
	ControllerRegisteredFunctionsTelemetryEvent,
	RegisteredFunction,
)


@pytest.mark.unit
class TestBaseTelemetryEventProperties:
	"""Test the properties method on concrete subclasses."""

	def test_agent_step_event_name(self):
		event = AgentStepTelemetryEvent(
			agent_id='abc123',
			step=1,
			step_error=[],
			consecutive_failures=0,
			actions=[],
		)
		assert event.name == 'agent_step'

	def test_agent_step_event_properties(self):
		event = AgentStepTelemetryEvent(
			agent_id='abc123',
			step=2,
			step_error=['timeout'],
			consecutive_failures=1,
			actions=[{'go_to_url': {'url': 'https://x.com'}}],
		)
		props = event.properties
		assert props['agent_id'] == 'abc123'
		assert props['step'] == 2
		assert props['step_error'] == ['timeout']
		assert props['consecutive_failures'] == 1

	def test_agent_run_event(self):
		event = AgentRunTelemetryEvent(
			agent_id='id1',
			use_vision=True,
			task='Do something',
			model_name='claude-3-5-sonnet',
			chat_model_library='ChatAnthropic',
			version='1.0.0',
			source='test',
		)
		assert event.name == 'agent_run'
		props = event.properties
		assert props['use_vision'] is True
		assert props['task'] == 'Do something'
		assert props['model_name'] == 'claude-3-5-sonnet'

	def test_agent_end_event(self):
		event = AgentEndTelemetryEvent(
			agent_id='id2',
			steps=5,
			max_steps_reached=False,
			success=True,
			errors=[],
		)
		assert event.name == 'agent_end'
		props = event.properties
		assert props['steps'] == 5
		assert props['success'] is True

	def test_controller_registered_functions_event(self):
		funcs = [RegisteredFunction(name='click', params={'index': 'int'})]
		event = ControllerRegisteredFunctionsTelemetryEvent(registered_functions=funcs)
		assert event.name == 'controller_registered_functions'
		props = event.properties
		assert 'registered_functions' in props


@pytest.mark.unit
class TestRegisteredFunction:
	def test_creation(self):
		func = RegisteredFunction(name='go_to_url', params={'url': 'str'})
		assert func.name == 'go_to_url'
		assert func.params == {'url': 'str'}


@pytest.mark.unit
class TestProductTelemetryDisabled:
	"""Test ProductTelemetry service behavior."""

	def test_capture_no_raises_with_disabled_client(self):
		"""capture() should not raise even if _posthog_client is None."""
		from browser_use.telemetry.service import ProductTelemetry

		# Get existing singleton and temporarily set client to None
		telemetry = ProductTelemetry()
		original_client = telemetry._posthog_client
		telemetry._posthog_client = None

		try:
			event = AgentStepTelemetryEvent(agent_id='x', step=1, step_error=[], consecutive_failures=0, actions=[])
			# Should not raise when client is None
			telemetry.capture(event)
		finally:
			telemetry._posthog_client = original_client  # restore

	def test_user_id_returns_string(self):
		"""user_id property should return a non-empty string."""
		from browser_use.telemetry.service import ProductTelemetry

		t = ProductTelemetry()
		uid = t.user_id
		assert isinstance(uid, str)
		assert len(uid) > 0

	def test_direct_capture_skips_when_no_client(self):
		"""_direct_capture does nothing if _posthog_client is None."""
		from browser_use.telemetry.service import ProductTelemetry

		telemetry = ProductTelemetry()
		original_client = telemetry._posthog_client
		telemetry._posthog_client = None

		try:
			event = AgentStepTelemetryEvent(agent_id='y', step=3, step_error=[], consecutive_failures=0, actions=[])
			# Should complete without error
			telemetry._direct_capture(event)
		finally:
			telemetry._posthog_client = original_client
