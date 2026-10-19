"""
Unit tests for browser_use/agent/views.py

Tests ActionResult, AgentBrain, AgentOutput, AgentHistory, AgentHistoryList,
AgentStepInfo, AgentError.
"""

import pytest
from pydantic import ValidationError

from browser_use.agent.views import (
	ActionResult,
	AgentBrain,
	AgentError,
	AgentHistory,
	AgentHistoryList,
	AgentOutput,
	AgentStepInfo,
)
from browser_use.browser.views import BrowserStateHistory, TabInfo


def _make_brain() -> AgentBrain:
	return AgentBrain(
		page_summary='Page with a login form',
		evaluation_previous_goal='Success',
		memory='Clicked login button',
		next_goal='Fill in credentials',
	)


def _make_history_state() -> BrowserStateHistory:
	return BrowserStateHistory(
		url='https://example.com',
		title='Example',
		tabs=[TabInfo(page_id=0, url='https://example.com', title='Example')],
		interacted_element=[None],
	)


@pytest.mark.unit
class TestActionResult:
	def test_default_values(self):
		result = ActionResult()
		assert result.is_done is False
		assert result.extracted_content is None
		assert result.error is None
		assert result.include_in_memory is False

	def test_success_result(self):
		result = ActionResult(extracted_content='Found it', include_in_memory=True)
		assert result.extracted_content == 'Found it'
		assert result.include_in_memory is True
		assert result.is_done is False

	def test_done_result(self):
		result = ActionResult(is_done=True, extracted_content='Task complete')
		assert result.is_done is True

	def test_error_result(self):
		result = ActionResult(error='Element not found', include_in_memory=True)
		assert result.error == 'Element not found'
		assert result.is_done is False

	def test_serialization(self):
		result = ActionResult(extracted_content='data', is_done=True)
		d = result.model_dump(exclude_none=True)
		assert 'extracted_content' in d
		assert 'is_done' in d


@pytest.mark.unit
class TestAgentBrain:
	def test_all_fields(self):
		brain = _make_brain()
		assert brain.page_summary == 'Page with a login form'
		assert brain.evaluation_previous_goal == 'Success'
		assert brain.memory == 'Clicked login button'
		assert brain.next_goal == 'Fill in credentials'

	def test_missing_field_raises(self):
		with pytest.raises(ValidationError):
			AgentBrain(
				page_summary='',
				evaluation_previous_goal='N/A',
				# missing memory and next_goal
			)

	def test_empty_strings_valid(self):
		brain = AgentBrain(
			page_summary='',
			evaluation_previous_goal='',
			memory='',
			next_goal='',
		)
		assert brain.page_summary == ''

	def test_serialization(self):
		brain = _make_brain()
		d = brain.model_dump()
		assert 'page_summary' in d
		assert 'evaluation_previous_goal' in d
		assert 'memory' in d
		assert 'next_goal' in d


@pytest.mark.unit
class TestAgentStepInfo:
	def test_basic_creation(self):
		info = AgentStepInfo(step_number=3, max_steps=10)
		assert info.step_number == 3
		assert info.max_steps == 10

	def test_step_number_zero(self):
		info = AgentStepInfo(step_number=0, max_steps=5)
		assert info.step_number == 0


@pytest.mark.unit
class TestAgentError:
	def test_format_validation_error(self):
		from pydantic import ValidationError as PE

		with pytest.raises(PE) as exc_info:
			AgentBrain(page_summary='', evaluation_previous_goal='')
		msg = AgentError.format_error(exc_info.value)
		assert AgentError.VALIDATION_ERROR in msg

	def test_format_generic_error(self):
		err = RuntimeError('Something broke')
		msg = AgentError.format_error(err)
		assert 'Something broke' in msg

	def test_constants_defined(self):
		assert AgentError.VALIDATION_ERROR
		assert AgentError.RATE_LIMIT_ERROR
		assert AgentError.NO_VALID_ACTION


@pytest.mark.unit
class TestAgentHistoryList:
	def test_empty_history(self):
		hist = AgentHistoryList(history=[])
		assert len(hist.history) == 0
		assert hist.is_done() is False

	def test_is_done_false_when_no_done_result(self):
		from browser_use.controller.registry.views import ActionModel

		state = _make_history_state()
		brain = _make_brain()

		# Create a minimal AgentOutput
		extended = AgentOutput.type_with_custom_actions(ActionModel)
		output = extended(current_state=brain, action=[])

		history_item = AgentHistory(
			model_output=output,
			result=[ActionResult(extracted_content='step1')],
			state=state,
		)
		hist = AgentHistoryList(history=[history_item])
		assert hist.is_done() is False

	def test_is_done_true_when_done_result(self):
		from browser_use.controller.registry.views import ActionModel

		state = _make_history_state()
		brain = _make_brain()
		extended = AgentOutput.type_with_custom_actions(ActionModel)
		output = extended(current_state=brain, action=[])

		history_item = AgentHistory(
			model_output=output,
			result=[ActionResult(is_done=True, extracted_content='done!')],
			state=state,
		)
		hist = AgentHistoryList(history=[history_item])
		assert hist.is_done() is True

	def test_final_result_none_when_empty(self):
		hist = AgentHistoryList(history=[])
		assert hist.final_result() is None

	def test_final_result_returns_last_done_content(self):
		from browser_use.controller.registry.views import ActionModel

		state = _make_history_state()
		brain = _make_brain()
		extended = AgentOutput.type_with_custom_actions(ActionModel)
		output = extended(current_state=brain, action=[])

		item = AgentHistory(
			model_output=output,
			result=[ActionResult(is_done=True, extracted_content='final answer')],
			state=state,
		)
		hist = AgentHistoryList(history=[item])
		assert hist.final_result() == 'final answer'
