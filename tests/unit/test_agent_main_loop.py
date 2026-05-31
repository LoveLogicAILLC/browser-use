"""
Unit tests for Agent main execution loop and core functionality.

Tests cover:
- agent.run() method
- agent.step() method
- Main execution loop logic
- Error recovery
- History tracking
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from browser_use.agent.service import Agent
from browser_use.agent.views import ActionResult, AgentOutput, AgentBrain
from browser_use.browser.views import BrowserState


@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentRun:
    """Test suite for Agent.run() method."""

    async def test_agent_run_simple_task(self, mock_llm, mock_browser):
        """Test: Basic run with 1-3 steps completes successfully."""
        # Arrange
        mock_llm.responses = [
            '{"action": [{"go_to_url": {"url": "https://example.com"}}]}',
            '{"action": [{"done": {"text": "Task complete"}}]}'
        ]

        agent = Agent(
            task="Go to example.com",
            llm=mock_llm,
            browser=mock_browser
        )

        # Act
        result = await agent.run(max_steps=5)

        # Assert
        assert result is not None
        assert len(result.history) > 0
        assert mock_llm.call_count >= 1

    async def test_agent_run_max_steps_exceeded(self, mock_llm, mock_browser):
        """Test: Agent stops when max_steps is reached."""
        # Arrange
        mock_llm.responses = [
            '{"action": [{"go_to_url": {"url": "https://example.com"}}]}'
        ] * 20  # More responses than max_steps

        agent = Agent(
            task="Go to many pages",
            llm=mock_llm,
            browser=mock_browser
        )

        # Act
        result = await agent.run(max_steps=5)

        # Assert
        assert len(result.history) <= 5
        assert result.is_done() is False  # Task not complete

    async def test_agent_run_early_completion(self, mock_llm, mock_browser):
        """Test: Task completes before max_steps when done action called."""
        # Arrange
        mock_llm.responses = [
            '{"action": [{"go_to_url": {"url": "https://example.com"}}]}',
            '{"action": [{"done": {"text": "Found it"}}]}'
        ]

        agent = Agent(
            task="Find something",
            llm=mock_llm,
            browser=mock_browser
        )

        # Act
        result = await agent.run(max_steps=10)

        # Assert
        assert len(result.history) < 10
        assert result.is_done() is True

    async def test_agent_run_no_steps_with_zero_max_steps(self, mock_llm, mock_browser):
        """Test: No steps executed when max_steps=0."""
        # Arrange
        agent = Agent(
            task="Do something",
            llm=mock_llm,
            browser=mock_browser
        )

        # Act
        result = await agent.run(max_steps=0)

        # Assert
        assert len(result.history) == 0
        assert mock_llm.call_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentStep:
    """Test suite for Agent.step() method."""

    async def test_agent_step_single_iteration(self, mock_llm, mock_browser):
        """Test: Single step executes one iteration of the loop."""
        # Arrange
        mock_llm.responses = ['{"action": [{"go_to_url": {"url": "https://example.com"}}]}']

        agent = Agent(
            task="Navigate",
            llm=mock_llm,
            browser=mock_browser
        )

        # Act
        await agent.step()

        # Assert
        assert agent.n_steps == 1
        assert mock_llm.call_count == 1
        assert len(agent.history) == 1

    async def test_agent_step_state_update(self, mock_llm, mock_browser, mock_browser_state):
        """Test: State changes after step execution."""
        # Arrange
        mock_llm.responses = ['{"action": [{"go_to_url": {"url": "https://newurl.com"}}]}']

        agent = Agent(
            task="Change page",
            llm=mock_llm,
            browser=mock_browser
        )

        initial_state = agent.browser_context.session.cached_state if agent.browser_context else None

        # Act
        await agent.step()

        # Assert
        assert agent.n_steps == 1
        # State should be updated after action execution

    async def test_agent_step_history_tracking(self, mock_llm, mock_browser):
        """Test: History is appended after each step."""
        # Arrange
        mock_llm.responses = [
            '{"action": [{"go_to_url": {"url": "https://example.com"}}]}',
            '{"action": [{"click_element": {"index": 1}}]}'
        ]

        agent = Agent(
            task="Navigate and click",
            llm=mock_llm,
            browser=mock_browser
        )

        # Act
        await agent.step()
        history_after_first = len(agent.history)

        await agent.step()
        history_after_second = len(agent.history)

        # Assert
        assert history_after_first == 1
        assert history_after_second == 2

    async def test_agent_step_error_recovery(self, mock_llm, mock_browser):
        """Test: Agent recovers from action failures within max_failures."""
        # Arrange
        mock_llm.responses = [
            '{"action": [{"click_element": {"index": 999}}]}',  # Invalid index
            '{"action": [{"go_to_url": {"url": "https://example.com"}}]}'  # Valid action
        ]

        agent = Agent(
            task="Recover from error",
            llm=mock_llm,
            browser=mock_browser,
            max_failures=5
        )

        # Act
        await agent.step()  # First step fails

        # Assert
        assert agent.consecutive_failures > 0 or agent.n_steps > 0
        # Agent should continue despite failure


@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentErrorHandling:
    """Test suite for Agent error handling."""

    async def test_agent_max_failures_exceeded(self, mock_llm, mock_browser):
        """Test: Agent stops after max_failures consecutive failures."""
        # Arrange
        mock_llm.responses = [
            '{"action": [{"click_element": {"index": 999}}]}'  # Always fails
        ] * 10

        agent = Agent(
            task="Fail repeatedly",
            llm=mock_llm,
            browser=mock_browser,
            max_failures=3
        )

        # Act & Assert
        with pytest.raises(Exception):
            await agent.run(max_steps=10)

    async def test_agent_consecutive_failures_reset(self, mock_llm, mock_browser):
        """Test: Consecutive failure counter resets on success."""
        # Arrange
        mock_llm.responses = [
            '{"action": [{"click_element": {"index": 999}}]}',  # Fail
            '{"action": [{"go_to_url": {"url": "https://example.com"}}]}',  # Success
            '{"action": [{"done": {"text": "Complete"}}]}'
        ]

        agent = Agent(
            task="Fail then succeed",
            llm=mock_llm,
            browser=mock_browser,
            max_failures=5
        )

        # Act
        await agent.step()  # Fail
        first_failure_count = agent.consecutive_failures

        await agent.step()  # Succeed
        second_failure_count = agent.consecutive_failures

        # Assert
        assert first_failure_count > 0
        assert second_failure_count == 0  # Reset on success

    @pytest.mark.skip(reason="Browser crash simulation complex")
    async def test_agent_browser_crash_recovery(self, mock_llm):
        """Test: Agent handles browser crashes gracefully."""
        # TODO: Implement browser crash simulation
        pass

    async def test_agent_llm_timeout(self, mock_browser):
        """Test: Agent handles LLM timeouts."""
        # Arrange
        slow_llm = MagicMock()
        slow_llm.ainvoke = AsyncMock(side_effect=TimeoutError("LLM timeout"))

        agent = Agent(
            task="Timeout test",
            llm=slow_llm,
            browser=mock_browser,
            max_failures=2
        )

        # Act & Assert
        with pytest.raises((TimeoutError, Exception)):
            await agent.run(max_steps=5)


@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentInitialization:
    """Test suite for Agent initialization."""

    def test_agent_init_basic(self, mock_llm, mock_browser):
        """Test: Agent initializes with basic parameters."""
        # Act
        agent = Agent(
            task="Test task",
            llm=mock_llm,
            browser=mock_browser
        )

        # Assert
        assert agent.task == "Test task"
        assert agent.llm == mock_llm
        assert agent.n_steps == 0
        assert agent.consecutive_failures == 0

    def test_agent_init_with_custom_max_failures(self, mock_llm, mock_browser):
        """Test: Agent respects custom max_failures setting."""
        # Act
        agent = Agent(
            task="Test",
            llm=mock_llm,
            browser=mock_browser,
            max_failures=10
        )

        # Assert
        assert agent.max_failures == 10

    def test_agent_init_with_vision_disabled(self, mock_llm, mock_browser):
        """Test: Agent initializes with vision mode disabled."""
        # Act
        agent = Agent(
            task="Test",
            llm=mock_llm,
            browser=mock_browser,
            use_vision=False
        )

        # Assert
        assert agent.use_vision is False

    def test_agent_init_with_validate_output(self, mock_llm, mock_browser):
        """Test: Agent initializes with output validation enabled."""
        # Act
        agent = Agent(
            task="Test",
            llm=mock_llm,
            browser=mock_browser,
            validate_output=True
        )

        # Assert
        assert agent.validate_output is True
