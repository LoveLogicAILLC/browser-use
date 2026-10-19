"""
Unit tests for browser_use/controller/views.py

Tests action input models for validation and field behavior.
"""

import pytest
from pydantic import ValidationError

from browser_use.controller.views import (
	ClickElementAction,
	DoneAction,
	GoToUrlAction,
	InputTextAction,
	NoParamsAction,
	OpenTabAction,
	ScrollAction,
	SearchGoogleAction,
	SendKeysAction,
	SwitchTabAction,
)


@pytest.mark.unit
class TestSearchGoogleAction:
	def test_valid_query(self):
		action = SearchGoogleAction(query='python testing')
		assert action.query == 'python testing'

	def test_empty_query(self):
		action = SearchGoogleAction(query='')
		assert action.query == ''

	def test_missing_query_raises(self):
		with pytest.raises(ValidationError):
			SearchGoogleAction()


@pytest.mark.unit
class TestGoToUrlAction:
	def test_valid_url(self):
		action = GoToUrlAction(url='https://example.com')
		assert action.url == 'https://example.com'

	def test_missing_url_raises(self):
		with pytest.raises(ValidationError):
			GoToUrlAction()


@pytest.mark.unit
class TestClickElementAction:
	def test_valid_index(self):
		action = ClickElementAction(index=5)
		assert action.index == 5
		assert action.xpath is None

	def test_with_xpath(self):
		action = ClickElementAction(index=3, xpath='//button[@id="submit"]')
		assert action.index == 3
		assert action.xpath == '//button[@id="submit"]'

	def test_missing_index_raises(self):
		with pytest.raises(ValidationError):
			ClickElementAction()


@pytest.mark.unit
class TestInputTextAction:
	def test_valid_input(self):
		action = InputTextAction(index=2, text='hello world')
		assert action.index == 2
		assert action.text == 'hello world'
		assert action.xpath is None

	def test_with_xpath(self):
		action = InputTextAction(index=1, text='test', xpath='//input[@name="q"]')
		assert action.xpath == '//input[@name="q"]'

	def test_missing_fields_raises(self):
		with pytest.raises(ValidationError):
			InputTextAction(index=1)  # missing text


@pytest.mark.unit
class TestDoneAction:
	def test_valid_done(self):
		action = DoneAction(text='Task completed successfully')
		assert action.text == 'Task completed successfully'

	def test_missing_text_raises(self):
		with pytest.raises(ValidationError):
			DoneAction()


@pytest.mark.unit
class TestSwitchTabAction:
	def test_valid_page_id(self):
		action = SwitchTabAction(page_id=2)
		assert action.page_id == 2

	def test_missing_page_id_raises(self):
		with pytest.raises(ValidationError):
			SwitchTabAction()


@pytest.mark.unit
class TestOpenTabAction:
	def test_valid_url(self):
		action = OpenTabAction(url='https://new-tab.com')
		assert action.url == 'https://new-tab.com'

	def test_missing_url_raises(self):
		with pytest.raises(ValidationError):
			OpenTabAction()


@pytest.mark.unit
class TestScrollAction:
	def test_scroll_no_amount(self):
		action = ScrollAction()
		assert action.amount is None

	def test_scroll_with_positive_amount(self):
		action = ScrollAction(amount=300)
		assert action.amount == 300

	def test_scroll_with_negative_amount(self):
		action = ScrollAction(amount=-200)
		assert action.amount == -200

	def test_scroll_with_zero_amount(self):
		action = ScrollAction(amount=0)
		assert action.amount == 0


@pytest.mark.unit
class TestSendKeysAction:
	def test_valid_keys(self):
		action = SendKeysAction(keys='Enter')
		assert action.keys == 'Enter'

	def test_keys_with_modifiers(self):
		action = SendKeysAction(keys='Control+a')
		assert action.keys == 'Control+a'

	def test_missing_keys_raises(self):
		with pytest.raises(ValidationError):
			SendKeysAction()


@pytest.mark.unit
class TestNoParamsAction:
	def test_no_params(self):
		action = NoParamsAction()
		assert action is not None

	def test_extra_params_discarded(self):
		action = NoParamsAction(foo='bar', baz=42)
		assert not hasattr(action, 'foo')
		assert not hasattr(action, 'baz')
