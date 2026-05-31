"""
Unit tests for browser_use/utils.py

Tests utility functions: timing decorators and singleton pattern.
"""
import asyncio
import time
import pytest
from browser_use.utils import time_execution_sync, time_execution_async, singleton


@pytest.mark.unit
class TestTimingDecorators:
    """Tests for timing decorator functions."""

    def test_time_execution_sync_basic(self):
        """Test: time_execution_sync decorator wraps sync function."""
        @time_execution_sync()
        def sample_function():
            time.sleep(0.01)
            return "result"

        result = sample_function()
        assert result == "result"

    def test_time_execution_sync_with_additional_text(self):
        """Test: time_execution_sync works with additional text."""
        @time_execution_sync("Testing")
        def sample_function():
            return "result"

        result = sample_function()
        assert result == "result"

    def test_time_execution_sync_with_args(self):
        """Test: time_execution_sync works with function arguments."""
        @time_execution_sync()
        def add_numbers(a, b):
            return a + b

        result = add_numbers(5, 3)
        assert result == 8

    def test_time_execution_sync_with_kwargs(self):
        """Test: time_execution_sync works with keyword arguments."""
        @time_execution_sync()
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = greet("Alice", greeting="Hi")
        assert result == "Hi, Alice!"

    def test_time_execution_sync_preserves_function_name(self):
        """Test: Decorator preserves function name (via functools.wraps)."""
        @time_execution_sync()
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    @pytest.mark.asyncio
    async def test_time_execution_async_basic(self):
        """Test: time_execution_async decorator wraps async function."""
        @time_execution_async()
        async def async_sample():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await async_sample()
        assert result == "async_result"

    @pytest.mark.asyncio
    async def test_time_execution_async_with_additional_text(self):
        """Test: time_execution_async works with additional text."""
        @time_execution_async("Async Testing")
        async def async_sample():
            return "result"

        result = await async_sample()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_time_execution_async_with_args(self):
        """Test: time_execution_async works with arguments."""
        @time_execution_async()
        async def async_multiply(x, y):
            await asyncio.sleep(0.001)
            return x * y

        result = await async_multiply(4, 5)
        assert result == 20

    @pytest.mark.asyncio
    async def test_time_execution_async_preserves_function_name(self):
        """Test: Async decorator preserves function name."""
        @time_execution_async()
        async def async_function():
            pass

        assert async_function.__name__ == "async_function"

    def test_time_execution_sync_with_exception(self):
        """Test: Sync decorator handles exceptions."""
        @time_execution_sync()
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

    @pytest.mark.asyncio
    async def test_time_execution_async_with_exception(self):
        """Test: Async decorator handles exceptions."""
        @time_execution_async()
        async def async_failing_function():
            raise ValueError("Async test error")

        with pytest.raises(ValueError, match="Async test error"):
            await async_failing_function()


@pytest.mark.unit
class TestSingletonDecorator:
    """Tests for singleton decorator pattern."""

    def test_singleton_creates_single_instance(self):
        """Test: Singleton decorator creates only one instance."""
        @singleton
        class TestClass:
            def __init__(self):
                self.value = 42

        instance1 = TestClass()
        instance2 = TestClass()

        assert instance1 is instance2
        assert id(instance1) == id(instance2)

    def test_singleton_multiple_classes(self):
        """Test: Different singleton classes have different instances."""
        @singleton
        class ClassA:
            def __init__(self):
                self.name = "A"

        @singleton
        class ClassB:
            def __init__(self):
                self.name = "B"

        a = ClassA()
        b = ClassB()

        assert a is not b
        assert a.name == "A"
        assert b.name == "B"

    def test_singleton_state_persists(self):
        """Test: State changes persist across singleton accesses."""
        @singleton
        class Counter:
            def __init__(self):
                self.count = 0

            def increment(self):
                self.count += 1

        counter1 = Counter()
        counter1.increment()
        counter1.increment()

        counter2 = Counter()
        assert counter2.count == 2

    def test_singleton_with_init_parameters_uses_first_call(self):
        """Test: Singleton uses parameters from first instantiation."""
        @singleton
        class ConfiguredClass:
            def __init__(self, value=10):
                self.value = value

        # First call with value=20
        instance1 = ConfiguredClass(value=20)
        # Second call with value=30 should return same instance
        instance2 = ConfiguredClass(value=30)

        assert instance1 is instance2
        assert instance1.value == 20  # First call's value persists

    def test_singleton_with_methods(self):
        """Test: Singleton preserves class methods."""
        @singleton
        class Calculator:
            def __init__(self):
                self.result = 0

            def add(self, x):
                self.result += x
                return self.result

        calc1 = Calculator()
        calc1.add(5)

        calc2 = Calculator()
        result = calc2.add(3)

        assert result == 8  # 5 + 3
        assert calc1 is calc2
