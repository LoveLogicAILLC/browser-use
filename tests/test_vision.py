"""
Simple try of the agent.

@dev You need to add OPENAI_API_KEY to your environment variables.
"""

import pytest

from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig

pytestmark = pytest.mark.skip(reason='integration test: requires OPENAI_API_KEY')


@pytest.mark.skip(reason='this is for local testing only')
async def test_vision():
	from pprint import pprint

	from langchain_openai import ChatOpenAI

	llm = ChatOpenAI(model='gpt-4o')
	controller = Controller()

	@controller.registry.action(description='explain what you see on the screen and ask user for input')
	async def explain_screen(text: str) -> str:
		pprint(text)
		answer = input('\nuser input next question: \n')
		return answer

	@controller.registry.action(description='done')
	async def done(text: str) -> str:
		return 'call explain_screen'

	agent = Agent(
		task=(
			'call explain_screen all the time the user asks you questions'
			' e.g. about the page like bbox which you see are labels'
			' - your task is to expalin it and get the next question'
		),
		llm=llm,
		controller=controller,
		browser=Browser(config=BrowserConfig(disable_security=True, headless=False)),
	)
	await agent.run(20)
