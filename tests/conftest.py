"""
Test configuration for browser-use.

This module provides comprehensive pytest fixtures for testing the browser-use library.
Includes mocks, factories, and test data generators.
"""
import asyncio
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from browser_use.agent.views import (
    ActionResult,
    AgentBrain,
    AgentHistory,
    AgentHistoryList,
    AgentOutput,
)
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext
from browser_use.browser.views import BrowserState, TabInfo
from browser_use.controller.registry.views import ActionModel
from browser_use.dom.views import DOMElementNode

# Import test helpers
from tests.utils.test_helpers import (
    MockLLM,
    MockBrowserState,
    MockActionResult,
    MockBrowser,
    create_mock_element,
)


# =============================================================================
# Event Loop Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# LLM Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def llm():
    """
    Fixture to provide a ChatOpenAI instance or a mock for testing.
    Uses a mock if OPENAI_API_KEY is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    logger.debug(f"API Key present: {bool(api_key)}")
    if not api_key:
        logger.debug("Using mock LLM for testing")
        # Return a mock LLM that returns predefined responses
        mock = MagicMock()
        mock.ainvoke = AsyncMock(return_value=AIMessage(
            content='{"action": [{"done": {"text": "Test completed"}}]}'
        ))
        return mock
    logger.debug("Using actual ChatOpenAI model")
    return ChatOpenAI(model='gpt-4o', api_key=api_key)


@pytest.fixture
def mock_llm():
    """Fixture for controllable mock LLM."""
    return MockLLM()


@pytest.fixture
def mock_llm_with_responses():
    """Factory fixture for creating mock LLM with custom responses."""
    def _create_mock(responses: List[str]):
        return MockLLM(responses=responses)
    return _create_mock


# =============================================================================
# Browser Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def browser():
    """
    Fixture to provide a Browser instance for testing.
    """
    logger.debug("Creating Browser instance for testing")
    return Browser(config=BrowserConfig(headless=True, disable_security=True))


@pytest.fixture(scope="function")
async def browser_context(browser):
    """
    Fixture to provide a BrowserContext instance for testing.
    """
    logger.debug("Creating BrowserContext instance for testing")
    context = BrowserContext(browser=browser)
    yield context
    await context.close()


@pytest.fixture
def mock_browser():
    """Fixture for mock browser without actual automation."""
    return MockBrowser()


@pytest.fixture
def mock_browser_state():
    """Fixture for creating mock browser states."""
    return MockBrowserState.create()


@pytest.fixture
def browser_state_factory():
    """Factory fixture for creating custom browser states."""
    def _create_state(
        url: str = "https://example.com",
        title: str = "Example Page",
        tabs: Optional[List[Dict[str, Any]]] = None,
        selector_map: Optional[Dict[int, Any]] = None,
    ) -> BrowserState:
        return MockBrowserState.create(
            url=url,
            title=title,
            tabs=tabs,
            selector_map=selector_map
        )
    return _create_state


# =============================================================================
# Action Result Fixtures
# =============================================================================

@pytest.fixture
def mock_action_result_success():
    """Fixture for successful action result."""
    return MockActionResult.success()


@pytest.fixture
def mock_action_result_error():
    """Fixture for error action result."""
    return MockActionResult.error()


@pytest.fixture
def mock_action_result_done():
    """Fixture for completion action result."""
    return MockActionResult.done()


@pytest.fixture
def action_result_factory():
    """Factory fixture for creating custom action results."""
    def _create_result(
        content: str = "Action completed",
        is_done: bool = False,
        error: Optional[str] = None,
        include_in_memory: bool = True
    ) -> ActionResult:
        if error:
            return ActionResult(error=error, include_in_memory=include_in_memory)
        return ActionResult(
            extracted_content=content,
            is_done=is_done,
            include_in_memory=include_in_memory
        )
    return _create_result


# =============================================================================
# DOM Element Fixtures
# =============================================================================

@pytest.fixture
def mock_dom_element():
    """Fixture for a simple mock DOM element."""
    return create_mock_element(
        index=1,
        tag='button',
        text='Click me'
    )


@pytest.fixture
def dom_element_factory():
    """Factory fixture for creating custom DOM elements."""
    return create_mock_element


@pytest.fixture
def mock_selector_map():
    """Fixture for a mock selector map with various elements."""
    return {
        1: create_mock_element(1, 'button', 'Submit'),
        2: create_mock_element(2, 'input', '', type='text', id='username'),
        3: create_mock_element(3, 'a', 'Click here', href='https://example.com'),
        4: create_mock_element(4, 'select', '', id='dropdown'),
        5: create_mock_element(5, 'textarea', '', id='comments'),
    }


# =============================================================================
# Agent History Fixtures
# =============================================================================

@pytest.fixture
def mock_agent_history():
    """Fixture for a simple agent history."""
    from tests.utils.test_helpers import TestDataBuilder
    return TestDataBuilder.build_agent_history(steps=3, success=True)


@pytest.fixture
def agent_history_factory():
    """Factory fixture for creating custom agent histories."""
    from tests.utils.test_helpers import TestDataBuilder
    def _create_history(
        steps: int = 3,
        success: bool = True,
        final_result: Optional[str] = None
    ) -> List[AgentHistory]:
        return TestDataBuilder.build_agent_history(
            steps=steps,
            success=success,
            final_result=final_result
        )
    return _create_history


# =============================================================================
# Test HTML Fixtures
# =============================================================================

@pytest.fixture
def simple_html():
    """Fixture for simple HTML page."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Test Header</h1>
        <button id="btn1">Click Me</button>
        <input type="text" id="input1" placeholder="Enter text">
        <a href="https://example.com">Link</a>
    </body>
    </html>
    """


@pytest.fixture
def complex_html():
    """Fixture for complex HTML page with nested elements."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Complex Test Page</title></head>
    <body>
        <nav>
            <ul>
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
            </ul>
        </nav>
        <main>
            <div class="container">
                <form id="testForm">
                    <input type="text" name="username" required>
                    <input type="password" name="password" required>
                    <select name="country">
                        <option value="us">United States</option>
                        <option value="uk">United Kingdom</option>
                    </select>
                    <button type="submit">Submit</button>
                </form>
            </div>
        </main>
    </body>
    </html>
    """


@pytest.fixture
def html_with_iframe():
    """Fixture for HTML with iframe."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Page with iFrame</title></head>
    <body>
        <h1>Main Page</h1>
        <iframe src="about:blank" id="testFrame"></iframe>
    </body>
    </html>
    """


# =============================================================================
# Temporary File Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Fixture for temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file():
    """Fixture for temporary file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        yield Path(f.name)
    # Cleanup
    if Path(f.name).exists():
        Path(f.name).unlink()


@pytest.fixture
def temp_json_file():
    """Fixture for temporary JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"test": "data"}, f)
        yield Path(f.name)
    # Cleanup
    if Path(f.name).exists():
        Path(f.name).unlink()


# =============================================================================
# Mock Message Fixtures
# =============================================================================

@pytest.fixture
def mock_ai_message():
    """Fixture for mock AI message."""
    return AIMessage(content='{"action": [{"go_to_url": {"url": "https://example.com"}}]}')


@pytest.fixture
def mock_ai_message_factory():
    """Factory fixture for creating custom AI messages."""
    def _create_message(content: str) -> AIMessage:
        return AIMessage(content=content)
    return _create_message


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def browser_config_headless():
    """Fixture for headless browser configuration."""
    return BrowserConfig(
        headless=True,
        disable_security=True,
        extra_chromium_args=['--no-sandbox']
    )


@pytest.fixture
def browser_config_visible():
    """Fixture for visible browser configuration."""
    return BrowserConfig(
        headless=False,
        disable_security=False
    )


# =============================================================================
# Sensitive Data Fixtures
# =============================================================================

@pytest.fixture
def sensitive_data_dict():
    """Fixture for sensitive data dictionary."""
    return {
        'password': 'secret123',
        'api_key': 'sk-test123',
        'token': 'bearer_token_xyz'
    }


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_urls():
    """Fixture for sample URLs."""
    return [
        'https://example.com',
        'https://google.com',
        'https://github.com',
        'https://stackoverflow.com',
    ]


@pytest.fixture
def sample_tasks():
    """Fixture for sample tasks."""
    return [
        "Go to example.com",
        "Search Google for 'browser automation'",
        "Find the pricing page",
        "Extract the main heading",
    ]


# =============================================================================
# Async Helpers
# =============================================================================

@pytest.fixture
def async_wait_helper():
    """Fixture for async wait helper."""
    from tests.utils.test_helpers import wait_for_condition
    return wait_for_condition


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "chaos: marks tests as chaos/fuzzing tests")
    config.addinivalue_line("markers", "property: marks tests as property-based tests")
    config.addinivalue_line("markers", "visual: marks tests as visual regression tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "performance: marks tests as performance/benchmark tests")
