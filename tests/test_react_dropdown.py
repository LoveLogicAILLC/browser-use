"""
Simple try of the agent.

@dev You need to add OPENAI_API_KEY to your environment variables.
"""

import asyncio

import pytest

from browser_use import Agent, AgentHistoryList
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext

pytestmark = pytest.mark.skip(reason='integration test: requires OPENAI_API_KEY')


async def test_dropdown():
	from langchain_openai import ChatOpenAI

	llm = ChatOpenAI(model='gpt-4o')
	agent = Agent(
		task=(
			'go to https://codepen.io/shyam-king/pen/ByBJoOv and select "Tiger" dropdown'
			' and read the text given in "Selected Animal" box (it can be empty as well)'
		),
		llm=llm,
		browser_context=BrowserContext(
			browser=Browser(config=BrowserConfig(headless=False, disable_security=True)),
		),
	)
	history: AgentHistoryList = await agent.run(10)

	result = history.final_result()
	assert result is not None
	print('result: ', result)


if __name__ == '__main__':
	asyncio.run(test_dropdown())
