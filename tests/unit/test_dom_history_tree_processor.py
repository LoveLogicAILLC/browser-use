"""
Unit tests for browser_use/dom/history_tree_processor/service.py

Tests hashing, element search, and comparison operations.
"""
import pytest
from browser_use.dom.history_tree_processor.service import HistoryTreeProcessor
from browser_use.dom.history_tree_processor.view import DOMHistoryElement
from browser_use.dom.views import DOMElementNode


def _make_element(
	tag: str = 'button',
	xpath: str = '//button',
	attributes: dict | None = None,
	parent: DOMElementNode | None = None,
	highlight_index: int | None = None,
) -> DOMElementNode:
	return DOMElementNode(
		tag_name=tag,
		is_visible=True,
		parent=parent,
		xpath=xpath,
		attributes=attributes or {},
		children=[],
		highlight_index=highlight_index,
	)


@pytest.mark.unit
class TestGetParentBranchPath:
	def test_root_element_has_empty_path(self):
		root = _make_element(tag='html')
		path = HistoryTreeProcessor._get_parent_branch_path(root)
		assert path == []

	def test_child_element_includes_parent_tags(self):
		root = _make_element(tag='html')
		body = _make_element(tag='body', parent=root)
		button = _make_element(tag='button', parent=body)

		path = HistoryTreeProcessor._get_parent_branch_path(button)
		assert path == ['body', 'button']

	def test_deep_nesting(self):
		root = _make_element(tag='html')
		div = _make_element(tag='div', parent=root)
		span = _make_element(tag='span', parent=div)
		a = _make_element(tag='a', parent=span)

		path = HistoryTreeProcessor._get_parent_branch_path(a)
		assert path == ['div', 'span', 'a']


@pytest.mark.unit
class TestHashingMethods:
	def test_parent_branch_path_hash_is_string(self):
		h = HistoryTreeProcessor._parent_branch_path_hash(['div', 'button'])
		assert isinstance(h, str)
		assert len(h) == 64  # SHA256 hex

	def test_same_paths_produce_same_hash(self):
		h1 = HistoryTreeProcessor._parent_branch_path_hash(['div', 'button'])
		h2 = HistoryTreeProcessor._parent_branch_path_hash(['div', 'button'])
		assert h1 == h2

	def test_different_paths_produce_different_hashes(self):
		h1 = HistoryTreeProcessor._parent_branch_path_hash(['div', 'button'])
		h2 = HistoryTreeProcessor._parent_branch_path_hash(['span', 'button'])
		assert h1 != h2

	def test_attributes_hash_is_string(self):
		h = HistoryTreeProcessor._attributes_hash({'class': 'btn', 'id': 'submit'})
		assert isinstance(h, str)
		assert len(h) == 64

	def test_same_attributes_produce_same_hash(self):
		h1 = HistoryTreeProcessor._attributes_hash({'class': 'btn'})
		h2 = HistoryTreeProcessor._attributes_hash({'class': 'btn'})
		assert h1 == h2

	def test_empty_attributes_hashes_cleanly(self):
		h = HistoryTreeProcessor._attributes_hash({})
		assert isinstance(h, str)

	def test_xpath_hash_is_string(self):
		h = HistoryTreeProcessor._xpath_hash('//button[@id="submit"]')
		assert isinstance(h, str)
		assert len(h) == 64

	def test_empty_xpath_hashes_cleanly(self):
		h = HistoryTreeProcessor._xpath_hash('')
		assert isinstance(h, str)


@pytest.mark.unit
class TestConvertDomElementToHistoryElement:
	def test_basic_conversion(self):
		root = _make_element(tag='html')
		button = _make_element(tag='button', xpath='//button', parent=root, highlight_index=1)

		history = HistoryTreeProcessor.convert_dom_element_to_history_element(button)
		assert isinstance(history, DOMHistoryElement)
		assert history.tag_name == 'button'
		assert history.xpath == '//button'

	def test_attributes_preserved(self):
		root = _make_element(tag='html')
		button = _make_element(
			tag='button',
			xpath='//button',
			attributes={'class': 'primary', 'id': 'btn'},
			parent=root,
			highlight_index=2,
		)
		history = HistoryTreeProcessor.convert_dom_element_to_history_element(button)
		assert history.attributes == {'class': 'primary', 'id': 'btn'}


@pytest.mark.unit
class TestFindHistoryElementInTree:
	def test_find_matching_element(self):
		root = _make_element(tag='html')
		button = _make_element(tag='button', xpath='//button', parent=root, highlight_index=5)
		root.children.append(button)

		history_el = HistoryTreeProcessor.convert_dom_element_to_history_element(button)
		found = HistoryTreeProcessor.find_history_element_in_tree(history_el, root)
		assert found is button

	def test_returns_none_when_not_found(self):
		root = _make_element(tag='html')
		# Create a history element from a different button
		other_button = _make_element(
			tag='button', xpath='//other', attributes={'id': 'x'}, highlight_index=99
		)
		history_el = HistoryTreeProcessor.convert_dom_element_to_history_element(other_button)

		found = HistoryTreeProcessor.find_history_element_in_tree(history_el, root)
		assert found is None


@pytest.mark.unit
class TestCompareHistoryAndDomElement:
	def test_same_element_matches(self):
		root = _make_element(tag='html')
		button = _make_element(
			tag='button', xpath='//button[@id="x"]', attributes={'id': 'x'}, parent=root, highlight_index=3
		)
		history_el = HistoryTreeProcessor.convert_dom_element_to_history_element(button)

		result = HistoryTreeProcessor.compare_history_element_and_dom_element(history_el, button)
		assert result is True

	def test_different_element_does_not_match(self):
		root = _make_element(tag='html')
		button1 = _make_element(tag='button', xpath='//button[1]', parent=root, highlight_index=1)
		button2 = _make_element(tag='button', xpath='//button[2]', parent=root, highlight_index=2)

		history_el = HistoryTreeProcessor.convert_dom_element_to_history_element(button1)
		result = HistoryTreeProcessor.compare_history_element_and_dom_element(history_el, button2)
		assert result is False
