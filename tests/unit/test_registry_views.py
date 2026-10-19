"""
Unit tests for browser_use/controller/registry/views.py

Tests RegisteredAction, ActionModel, ActionRegistry.
"""

import pytest
from pydantic import BaseModel

from browser_use.controller.registry.views import (
	ActionModel,
	ActionRegistry,
	RegisteredAction,
)


class ClickParams(BaseModel):
	index: int
	description: str = ''


class DoneParams(BaseModel):
	success: bool = True


@pytest.mark.unit
class TestRegisteredAction:
	def _make_action(self, name='click', description='Click an element') -> RegisteredAction:
		return RegisteredAction(
			name=name,
			description=description,
			function=lambda: None,
			param_model=ClickParams,
		)

	def test_creation(self):
		action = self._make_action()
		assert action.name == 'click'
		assert action.description == 'Click an element'

	def test_prompt_description_contains_name(self):
		action = self._make_action(name='go_to_url', description='Navigate to URL')
		desc = action.prompt_description()
		assert 'go_to_url' in desc
		assert 'Navigate to URL' in desc

	def test_prompt_description_contains_params(self):
		action = self._make_action()
		desc = action.prompt_description()
		assert 'index' in desc

	def test_prompt_description_excludes_title(self):
		action = self._make_action()
		desc = action.prompt_description()
		assert 'title' not in desc


@pytest.mark.unit
class TestActionRegistry:
	def test_empty_registry(self):
		registry = ActionRegistry()
		assert registry.actions == {}

	def test_get_prompt_description_empty(self):
		registry = ActionRegistry()
		assert registry.get_prompt_description() == ''

	def test_get_prompt_description_with_actions(self):
		registry = ActionRegistry()
		action = RegisteredAction(
			name='click',
			description='Click element',
			function=lambda: None,
			param_model=ClickParams,
		)
		registry.actions['click'] = action
		desc = registry.get_prompt_description()
		assert 'click' in desc
		assert 'Click element' in desc

	def test_multiple_actions_in_description(self):
		registry = ActionRegistry()
		registry.actions['click'] = RegisteredAction(
			name='click', description='Click', function=lambda: None, param_model=ClickParams
		)
		registry.actions['done'] = RegisteredAction(
			name='done', description='Done', function=lambda: None, param_model=DoneParams
		)
		desc = registry.get_prompt_description()
		assert 'click' in desc
		assert 'done' in desc


@pytest.mark.unit
class TestActionModel:
	def test_get_index_returns_none_when_empty(self):
		model = ActionModel()
		assert model.get_index() is None

	def test_base_action_model_serializable(self):
		model = ActionModel()
		data = model.model_dump()
		assert isinstance(data, dict)

	def test_dynamic_action_model_with_index(self):
		"""Test ActionModel subclass with an index field."""
		from pydantic import create_model

		DynamicModel = create_model(
			'DynamicModel',
			__base__=ActionModel,
			click=(ClickParams | None, None),
		)
		instance = DynamicModel(click=ClickParams(index=7))
		assert instance.get_index() == 7

	def test_set_index_on_dynamic_model(self):
		from pydantic import create_model

		DynamicModel = create_model(
			'DynamicModel',
			__base__=ActionModel,
			click=(ClickParams | None, None),
		)
		instance = DynamicModel(click=ClickParams(index=1))
		instance.set_index(42)
		assert instance.click.index == 42
