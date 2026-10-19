"""
Unit tests for browser_use/browser/views.py

Tests BrowserState, TabInfo, BrowserStateHistory, and related error types.
"""

import pytest
from pydantic import ValidationError

from browser_use.browser.views import (
	BrowserError,
	BrowserState,
	BrowserStateHistory,
	TabInfo,
	URLNotAllowedError,
)
from browser_use.dom.views import DOMElementNode


def _make_root_element() -> DOMElementNode:
	return DOMElementNode(
		tag_name='html',
		is_visible=True,
		parent=None,
		xpath='',
		attributes={},
		children=[],
	)


@pytest.mark.unit
class TestTabInfo:
	def test_valid_tab(self):
		tab = TabInfo(page_id=0, url='https://example.com', title='Example')
		assert tab.page_id == 0
		assert tab.url == 'https://example.com'
		assert tab.title == 'Example'

	def test_missing_fields_raises(self):
		with pytest.raises(ValidationError):
			TabInfo(page_id=0)  # missing url and title

	def test_tab_serialization(self):
		tab = TabInfo(page_id=1, url='https://test.com', title='Test')
		data = tab.model_dump()
		assert data['page_id'] == 1
		assert data['url'] == 'https://test.com'
		assert data['title'] == 'Test'


@pytest.mark.unit
class TestBrowserState:
	def _make_state(self, url: str = 'https://example.com') -> BrowserState:
		return BrowserState(
			url=url,
			title='Test Page',
			tabs=[TabInfo(page_id=0, url=url, title='Test Page')],
			screenshot='',
			element_tree=_make_root_element(),
			selector_map={},
		)

	def test_create_basic_state(self):
		state = self._make_state()
		assert state.url == 'https://example.com'
		assert state.title == 'Test Page'
		assert len(state.tabs) == 1

	def test_screenshot_optional(self):
		state = self._make_state()
		assert state.screenshot == ''

	def test_url_stored_correctly(self):
		state = self._make_state('https://different-url.com/path?q=1')
		assert state.url == 'https://different-url.com/path?q=1'

	def test_pixels_above_below_defaults(self):
		state = self._make_state()
		assert state.pixels_above == 0
		assert state.pixels_below == 0

	def test_browser_errors_default_empty(self):
		state = self._make_state()
		assert state.browser_errors == []

	def test_multiple_tabs(self):
		state = BrowserState(
			url='https://tab1.com',
			title='Tab 1',
			tabs=[
				TabInfo(page_id=0, url='https://tab1.com', title='Tab 1'),
				TabInfo(page_id=1, url='https://tab2.com', title='Tab 2'),
			],
			screenshot='',
			element_tree=_make_root_element(),
			selector_map={},
		)
		assert len(state.tabs) == 2


@pytest.mark.unit
class TestBrowserStateHistory:
	def test_to_dict_structure(self):
		history = BrowserStateHistory(
			url='https://example.com',
			title='Example',
			tabs=[TabInfo(page_id=0, url='https://example.com', title='Example')],
			interacted_element=[None],
			screenshot='base64data',
		)
		d = history.to_dict()
		assert 'url' in d
		assert 'title' in d
		assert 'tabs' in d
		assert 'screenshot' in d
		assert 'interacted_element' in d

	def test_to_dict_tabs_serialized(self):
		history = BrowserStateHistory(
			url='https://x.com',
			title='X',
			tabs=[TabInfo(page_id=0, url='https://x.com', title='X')],
			interacted_element=[None],
		)
		d = history.to_dict()
		assert isinstance(d['tabs'], list)
		assert d['tabs'][0]['url'] == 'https://x.com'


@pytest.mark.unit
class TestBrowserErrors:
	def test_browser_error_is_exception(self):
		err = BrowserError('test error')
		assert isinstance(err, Exception)
		assert str(err) == 'test error'

	def test_url_not_allowed_is_browser_error(self):
		err = URLNotAllowedError('https://blocked.com')
		assert isinstance(err, BrowserError)
		assert isinstance(err, Exception)

	def test_url_not_allowed_inherits_from_browser_error(self):
		err = URLNotAllowedError('blocked')
		assert isinstance(err, BrowserError)
		assert str(err) == 'blocked'
