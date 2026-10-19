"""
Simple try of the agent.

@dev You need to add OPENAI_API_KEY to your environment variables.
"""

import os

import pytest

from browser_use import Agent, AgentHistoryList
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext

pytestmark = pytest.mark.skip(reason='integration test: requires OPENAI_API_KEY')


async def test_gif_path():
	from langchain_openai import ChatOpenAI

	if os.path.exists('./google.gif'):
		os.unlink('./google.gif')

	llm = ChatOpenAI(model='gpt-4o')
	agent = Agent(
		task=('go to google.com and search for text "hi there"'),
		llm=llm,
		browser_context=BrowserContext(
			browser=Browser(config=BrowserConfig(headless=False, disable_security=True)),
		),
		generate_gif='./google.gif',
	)

	history: AgentHistoryList = await agent.run(20)

	result = history.final_result()
	assert result is not None
	assert os.path.exists('./google.gif'), 'google.gif was not created'
