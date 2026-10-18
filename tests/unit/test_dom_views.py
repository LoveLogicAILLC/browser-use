"""
Unit tests for browser_use/dom/views.py

Tests DOMTextNode, DOMElementNode methods (pure Python, no browser needed).
"""
import pytest
from browser_use.dom.views import DOMElementNode, DOMState, DOMTextNode, SelectorMap


def _make_element(
	tag: str = 'div',
	xpath: str = '//div',
	attributes: dict | None = None,
	parent: DOMElementNode | None = None,
	highlight_index: int | None = None,
	is_interactive: bool = False,
	is_top_element: bool = False,
	shadow_root: bool = False,
) -> DOMElementNode:
	return DOMElementNode(
		tag_name=tag,
		is_visible=True,
		parent=parent,
		xpath=xpath,
		attributes=attributes or {},
		children=[],
		highlight_index=highlight_index,
		is_interactive=is_interactive,
		is_top_element=is_top_element,
		shadow_root=shadow_root,
	)


def _make_text(text: str, parent: DOMElementNode | None = None) -> DOMTextNode:
	return DOMTextNode(text=text, is_visible=True, parent=parent)


@pytest.mark.unit
class TestDOMTextNodeHasParentWithHighlightIndex:
	def test_no_parent_returns_false(self):
		node = _make_text('hello', parent=None)
		assert node.has_parent_with_highlight_index() is False

	def test_parent_without_highlight_returns_false(self):
		parent = _make_element(highlight_index=None)
		node = _make_text('hello', parent=parent)
		assert node.has_parent_with_highlight_index() is False

	def test_parent_with_highlight_returns_true(self):
		parent = _make_element(highlight_index=3)
		node = _make_text('hello', parent=parent)
		assert node.has_parent_with_highlight_index() is True

	def test_grandparent_with_highlight_returns_true(self):
		grandparent = _make_element(highlight_index=7)
		parent = _make_element(parent=grandparent, highlight_index=None)
		node = _make_text('hello', parent=parent)
		assert node.has_parent_with_highlight_index() is True

	def test_type_attribute_is_text_node(self):
		node = _make_text('abc')
		assert node.type == 'TEXT_NODE'


@pytest.mark.unit
class TestDOMElementNodeRepr:
	def test_simple_tag(self):
		el = _make_element(tag='button', attributes={})
		r = repr(el)
		assert r.startswith('<button>')

	def test_attributes_in_repr(self):
		el = _make_element(tag='a', attributes={'href': '/home', 'class': 'link'})
		r = repr(el)
		assert 'href="/home"' in r
		assert 'class="link"' in r

	def test_interactive_flag(self):
		el = _make_element(tag='button', is_interactive=True)
		r = repr(el)
		assert 'interactive' in r

	def test_top_element_flag(self):
		el = _make_element(tag='div', is_top_element=True)
		r = repr(el)
		assert 'top' in r

	def test_shadow_root_flag(self):
		el = _make_element(tag='div', shadow_root=True)
		r = repr(el)
		assert 'shadow-root' in r

	def test_highlight_index_in_repr(self):
		el = _make_element(tag='span', highlight_index=5)
		r = repr(el)
		assert 'highlight:5' in r

	def test_no_extras_no_brackets(self):
		el = _make_element(tag='div')
		r = repr(el)
		assert '[' not in r

	def test_multiple_extras(self):
		el = _make_element(tag='div', is_interactive=True, is_top_element=True, highlight_index=2)
		r = repr(el)
		assert 'interactive' in r
		assert 'top' in r
		assert 'highlight:2' in r


@pytest.mark.unit
class TestGetAllTextTillNextClickable:
	def test_empty_children(self):
		el = _make_element()
		assert el.get_all_text_till_next_clickable_element() == ''

	def test_single_text_child(self):
		el = _make_element()
		text = _make_text('Hello', parent=el)
		el.children.append(text)
		assert el.get_all_text_till_next_clickable_element() == 'Hello'

	def test_multiple_text_children(self):
		el = _make_element()
		el.children.append(_make_text('Hello', parent=el))
		el.children.append(_make_text('World', parent=el))
		result = el.get_all_text_till_next_clickable_element()
		assert 'Hello' in result
		assert 'World' in result

	def test_stops_at_highlighted_child(self):
		el = _make_element()
		el.children.append(_make_text('visible', parent=el))
		# A highlighted child element should stop collection
		highlighted_child = _make_element(tag='button', highlight_index=1, parent=el)
		highlighted_child.children.append(_make_text('inside button', parent=highlighted_child))
		el.children.append(highlighted_child)
		result = el.get_all_text_till_next_clickable_element()
		assert 'visible' in result
		assert 'inside button' not in result

	def test_nested_non_highlighted(self):
		outer = _make_element()
		inner = _make_element(tag='span', parent=outer)
		inner.children.append(_make_text('nested', parent=inner))
		outer.children.append(inner)
		assert 'nested' in outer.get_all_text_till_next_clickable_element()

	def test_max_depth_zero(self):
		el = _make_element()
		child = _make_element(tag='span', parent=el)
		child.children.append(_make_text('deep', parent=child))
		el.children.append(child)
		result = el.get_all_text_till_next_clickable_element(max_depth=0)
		# depth 0 means only self is processed, text is at depth 1 inside a child
		assert result == ''

	def test_max_depth_one(self):
		el = _make_element()
		child = _make_element(tag='span', parent=el)
		text_node = _make_text('level1', parent=child)
		child.children.append(text_node)
		el.children.append(child)
		result = el.get_all_text_till_next_clickable_element(max_depth=1)
		# child is at depth 1, its text child is at depth 2 which exceeds max_depth=1
		assert 'level1' not in result

	def test_whitespace_stripped(self):
		el = _make_element()
		el.children.append(_make_text('  ', parent=el))
		result = el.get_all_text_till_next_clickable_element()
		assert result == ''


@pytest.mark.unit
class TestClickableElementsToString:
	def test_empty_tree(self):
		el = _make_element()
		assert el.clickable_elements_to_string() == ''

	def test_element_with_highlight_included(self):
		root = _make_element()
		btn = _make_element(tag='button', highlight_index=1, parent=root)
		root.children.append(btn)
		result = root.clickable_elements_to_string()
		assert '[1]<button>' in result

	def test_text_without_highlighted_parent(self):
		root = _make_element()
		text = _make_text('free text', parent=root)
		root.children.append(text)
		result = root.clickable_elements_to_string()
		assert '[]free text' in result

	def test_text_with_highlighted_parent_not_duplicated(self):
		root = _make_element()
		btn = _make_element(tag='button', highlight_index=2, parent=root)
		inner_text = _make_text('click me', parent=btn)
		btn.children.append(inner_text)
		root.children.append(btn)
		result = root.clickable_elements_to_string()
		# Text appears inside the button's entry but NOT as a separate []text line
		assert '[2]<button>click me</button>' in result
		assert '[]click me' not in result

	def test_include_attributes_filter(self):
		root = _make_element()
		btn = _make_element(
			tag='button',
			highlight_index=3,
			attributes={'class': 'primary', 'id': 'submit', 'data-test': 'btn'},
			parent=root,
		)
		root.children.append(btn)
		result = root.clickable_elements_to_string(include_attributes=['class'])
		assert 'class="primary"' in result
		assert 'id=' not in result

	def test_multiple_highlighted_elements(self):
		root = _make_element()
		a = _make_element(tag='a', highlight_index=1, parent=root)
		b = _make_element(tag='button', highlight_index=2, parent=root)
		root.children.append(a)
		root.children.append(b)
		result = root.clickable_elements_to_string()
		assert '[1]<a>' in result
		assert '[2]<button>' in result


@pytest.mark.unit
class TestGetFileUploadElement:
	def test_self_is_file_input(self):
		el = _make_element(tag='input', attributes={'type': 'file'})
		assert el.get_file_upload_element() is el

	def test_child_is_file_input(self):
		parent = _make_element(tag='div')
		child = _make_element(tag='input', attributes={'type': 'file'}, parent=parent)
		parent.children.append(child)
		assert parent.get_file_upload_element() is child

	def test_sibling_is_file_input(self):
		grandparent = _make_element(tag='div')
		btn = _make_element(tag='button', parent=grandparent)
		file_input = _make_element(
			tag='input', attributes={'type': 'file'}, parent=grandparent
		)
		grandparent.children.append(btn)
		grandparent.children.append(file_input)
		assert btn.get_file_upload_element() is file_input

	def test_returns_none_when_no_file_input(self):
		el = _make_element(tag='div')
		assert el.get_file_upload_element() is None

	def test_non_file_input_not_returned(self):
		el = _make_element(tag='input', attributes={'type': 'text'})
		assert el.get_file_upload_element() is None

	def test_check_siblings_false_skips_siblings(self):
		grandparent = _make_element(tag='div')
		btn = _make_element(tag='button', parent=grandparent)
		file_input = _make_element(
			tag='input', attributes={'type': 'file'}, parent=grandparent
		)
		grandparent.children.append(btn)
		grandparent.children.append(file_input)
		# With check_siblings=False, siblings should NOT be checked
		assert btn.get_file_upload_element(check_siblings=False) is None


@pytest.mark.unit
class TestDOMStateAndSelectorMap:
	def test_dom_state_creation(self):
		root = _make_element(tag='html')
		state = DOMState(element_tree=root, selector_map={})
		assert state.element_tree is root
		assert state.selector_map == {}

	def test_selector_map_with_elements(self):
		root = _make_element(tag='html')
		btn = _make_element(tag='button', highlight_index=5)
		selector_map: SelectorMap = {5: btn}
		state = DOMState(element_tree=root, selector_map=selector_map)
		assert state.selector_map[5] is btn
