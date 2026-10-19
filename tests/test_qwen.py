import asyncio

import pytest

from browser_use.agent.service import Agent
from browser_use.agent.views import AgentHistoryList
from browser_use.browser.browser import Browser, BrowserConfig

pytest.importorskip('langchain_ollama', reason='integration test: requires Ollama')

from langchain_ollama import ChatOllama  # noqa: E402

pytestmark = pytest.mark.skip(reason='integration test: requires Ollama with Qwen model')


@pytest.fixture
def llm():
	return ChatOllama(
		model='qwen2.5:latest',
		num_ctx=128000,
	)


@pytest.fixture(scope='session')
def event_loop():
	loop = asyncio.get_event_loop_policy().new_event_loop()
	yield loop
	loop.close()


@pytest.fixture(scope='session')
async def browser(event_loop):
	browser_instance = Browser(config=BrowserConfig(headless=True))
	yield browser_instance
	await browser_instance.close()


@pytest.fixture
async def context(browser):
	async with await browser.new_context() as context:
		yield context


@pytest.mark.asyncio
async def test_qwen_model(llm, context):
	"""Test Qwen model via Ollama."""
	agent = Agent(
		task="Search Google for 'OpenAI'.",
		llm=llm,
		browser_context=context,
	)
	history: AgentHistoryList = await agent.run(max_steps=2)
	action_names = history.action_names()
	assert len(action_names) > 0
