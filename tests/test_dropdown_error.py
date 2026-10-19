"""
Simple try of the agent.

@dev You need to add OPENAI_API_KEY to your environment variables.
"""

import pytest

from browser_use import Agent, AgentHistoryList
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext

pytestmark = pytest.mark.skip(reason='integration test: requires OPENAI_API_KEY')


async def test_dropdown():
	from langchain_openai import ChatOpenAI

	llm = ChatOpenAI(model='gpt-4o')
	agent = Agent(
		task=('go to https://codepen.io/shyam-king/pen/emOyjKm and select number "4" and return the output of "selected value"'),
		llm=llm,
		browser_context=BrowserContext(
			browser=Browser(config=BrowserConfig(headless=False, disable_security=True)),
		),
	)
	history: AgentHistoryList = await agent.run(20)

	result = history.final_result()
	assert result is not None
	assert '4' in result
	print(result)
