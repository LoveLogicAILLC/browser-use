"""
Unit tests for Agent main execution loop and core functionality.

Tests cover:
- agent.run() method
- agent.step() method
- Main execution loop logic
- History tracking
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage

from browser_use.agent.service import Agent
from browser_use.agent.views import AgentBrain, AgentOutput
from browser_use.browser.views import BrowserState, TabInfo
from browser_use.dom.views import DOMElementNode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_browser_state(url: str = 'https://example.com') -> BrowserState:
	root = DOMElementNode(
		tag_name='html', is_visible=True, parent=None, xpath='', attributes={}, children=[]
	)
	return BrowserState(
		url=url,
		title='Test Page',
		tabs=[TabInfo(page_id=0, url=url, title='Test Page')],
		screenshot='',
		element_tree=root,
		selector_map={},
	)


def _make_mock_browser_context(url: str = 'https://example.com') -> MagicMock:
	ctx = MagicMock()
	ctx.get_state = AsyncMock(return_value=_make_browser_state(url))
	ctx.close = AsyncMock()
	ctx.session = None
	# Controller.multi_act awaits these methods
	ctx.get_session = AsyncMock(return_value=MagicMock(cached_state=MagicMock(selector_map={})))
	ctx.remove_highlights = AsyncMock()
	return ctx


def _make_base_llm() -> MagicMock:
	"""Create a MagicMock LLM with non-MagicMock model names to avoid routing issues."""
	llm = MagicMock()
	llm.model_name = 'mock-model'
	llm.model = 'mock-model'
	structured = MagicMock()
	structured.ainvoke = AsyncMock(return_value={'parsed': None, 'raw': AIMessage(content='')})
	llm.with_structured_output = MagicMock(return_value=structured)
	return llm


def _make_agent(task: str = 'Test', **kwargs) -> Agent:
	"""Create an agent with a mocked browser context."""
	ctx = _make_mock_browser_context()
	llm = _make_base_llm()
	return Agent(task=task, llm=llm, browser_context=ctx, **kwargs)


def _mock_get_next_action(agent: Agent) -> None:
	"""Patch agent.get_next_action and controller to return valid results."""
	from browser_use.agent.views import ActionResult

	brain = AgentBrain(
		page_summary='',
		evaluation_previous_goal='N/A',
		memory='',
		next_goal='continue',
	)
	# Use the agent's own AgentOutput type (extended with custom actions)
	output = agent.AgentOutput(current_state=brain, action=[])

	# Wrap in a side_effect that also increments n_steps (as the real method does)
	async def _get_next_action_stub(input_messages):
		agent.n_steps += 1
		return output

	agent.get_next_action = _get_next_action_stub
	# multi_act with empty actions returns [], so history is never written.
	# Patch controller.multi_act to return a non-empty result.
	agent.controller.multi_act = AsyncMock(
		return_value=[ActionResult(extracted_content='ok', include_in_memory=True)]
	)


# ---------------------------------------------------------------------------
# Initialization tests (sync)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAgentInitialization:
	"""Test suite for Agent initialization."""

	def test_agent_init_basic(self):
		"""Test: Agent initializes with basic parameters."""
		agent = _make_agent(task='Test task')

		assert agent.task == 'Test task'
		assert agent.n_steps == 1  # Agent starts step counter at 1
		assert agent.consecutive_failures == 0

	def test_agent_init_with_custom_max_failures(self):
		"""Test: Agent respects custom max_failures setting."""
		agent = _make_agent(max_failures=10)
		assert agent.max_failures == 10

	def test_agent_init_with_vision_disabled(self):
		"""Test: Agent initializes with vision mode disabled."""
		agent = _make_agent(use_vision=False)
		assert agent.use_vision is False

	def test_agent_init_with_validate_output(self):
		"""Test: Agent initializes with output validation enabled."""
		agent = _make_agent(validate_output=True)
		assert agent.validate_output is True

	def test_agent_init_task_stored(self):
		"""Test: Task is stored correctly."""
		agent = _make_agent(task='My specific task')
		assert agent.task == 'My specific task'


# ---------------------------------------------------------------------------
# Step tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentStep:
	"""Test suite for Agent.step() method."""

	async def test_agent_step_increments_n_steps(self):
		"""Test: n_steps increments after each successful step."""
		agent = _make_agent()
		_mock_get_next_action(agent)

		before = agent.n_steps
		await agent.step()
		assert agent.n_steps == before + 1

		await agent.step()
		assert agent.n_steps == before + 2

	async def test_agent_step_history_tracking(self):
		"""Test: History is appended after each step."""
		agent = _make_agent()
		_mock_get_next_action(agent)

		await agent.step()
		assert len(agent.history.history) == 1

		await agent.step()
		assert len(agent.history.history) == 2

	async def test_agent_step_resets_consecutive_failures_on_success(self):
		"""Test: consecutive_failures resets to 0 after a successful step."""
		agent = _make_agent()
		_mock_get_next_action(agent)
		agent.consecutive_failures = 2

		await agent.step()
		assert agent.consecutive_failures == 0


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentRun:
	"""Test suite for Agent.run() method."""

	async def test_agent_run_no_steps_with_zero_max_steps(self):
		"""Test: No steps executed when max_steps=0."""
		agent = _make_agent()
		_mock_get_next_action(agent)

		result = await agent.run(max_steps=0)
		assert len(result.history) == 0

	async def test_agent_run_respects_max_steps(self):
		"""Test: Agent stops after max_steps."""
		agent = _make_agent()
		_mock_get_next_action(agent)

		result = await agent.run(max_steps=3)
		assert len(result.history) <= 3

	async def test_agent_run_returns_history_object(self):
		"""Test: run() returns an AgentHistoryList."""
		agent = _make_agent()
		_mock_get_next_action(agent)

		result = await agent.run(max_steps=2)
		assert result is not None
		assert hasattr(result, 'history')

	async def test_agent_run_exact_step_count(self):
		"""Test: run() executes exactly max_steps steps."""
		agent = _make_agent()
		_mock_get_next_action(agent)

		result = await agent.run(max_steps=2)
		assert len(result.history) == 2


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentErrorHandling:
	"""Test suite for Agent error handling."""

	async def test_agent_stops_after_max_failures(self):
		"""Test: Agent stops cleanly after max_failures consecutive failures."""
		agent = _make_agent(max_failures=2)
		# Inject a failing get_next_action
		agent.get_next_action = AsyncMock(side_effect=Exception('Simulated LLM error'))

		result = await agent.run(max_steps=10)
		# Stopped early due to failures
		assert len(result.history) < 10

	async def test_agent_consecutive_failures_tracked(self):
		"""Test: consecutive_failures counter increases on step errors."""
		agent = _make_agent(max_failures=5)
		agent.get_next_action = AsyncMock(side_effect=ValueError('Parse error'))

		await agent.step()
		assert agent.consecutive_failures == 1

	@pytest.mark.skip(reason='Browser crash simulation complex')
	async def test_agent_browser_crash_recovery(self):
		"""Test: Agent handles browser crashes gracefully."""
		pass
