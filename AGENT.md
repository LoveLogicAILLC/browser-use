# Browser-Use Agent Documentation

**Version:** 0.1.37  
**Type:** AI-Powered Browser Automation Library  
**Language:** Python 3.11+  
**License:** MIT

---

## Overview

Browser-Use is a Python library that enables AI agents to control web browsers through natural language instructions. It combines LLM reasoning with Playwright browser automation to execute complex web tasks autonomously.

### Core Capabilities

- **Natural Language Task Execution**: Describe what you want done, the agent figures out how
- **Multi-Step Workflows**: Plan and execute complex sequences of browser actions
- **Visual Understanding**: Process screenshots to understand page layouts
- **Error Recovery**: Automatically retry and adapt when actions fail
- **Multi-Browser Support**: Chrome, Chromium, Edge, Firefox
- **LLM Flexibility**: Works with OpenAI, Anthropic, Google, AWS, local models

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER TASK                            │
│             "Find 3 laptops under $1000"                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATOR                        │
│  • Plan steps          • Manage context                     │
│  • Execute loop        • Track history                      │
│  • Error recovery      • Generate GIFs                      │
└────────┬────────────────────────────┬───────────────────────┘
         │                            │
         ▼                            ▼
┌──────────────────┐         ┌──────────────────────┐
│   LLM REASONING  │         │  BROWSER CONTEXT     │
│  • Parse state   │◄───────►│  • Navigate pages    │
│  • Decide action │         │  • Extract DOM       │
│  • Extract data  │         │  • Take screenshots  │
└──────────────────┘         └──────────┬───────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐         ┌──────────────────────┐
│  ACTION REGISTRY │         │   DOM PROCESSOR      │
│  • Click         │         │  • Build tree        │
│  • Type          │         │  • Track changes     │
│  • Navigate      │         │  • Index elements    │
│  • Custom actions│         │  • Highlight boxes   │
└──────────────────┘         └──────────────────────┘
```

---

## Key Components

### 1. Agent (`browser_use/agent/service.py`)

**Responsibility**: Orchestrates the entire task execution loop

**Main Loop**:
1. Get current browser state (DOM + screenshot)
2. Send state to LLM with task context
3. Parse LLM response into actions
4. Execute actions via controller
5. Capture results and update history
6. Repeat until task complete or max steps reached

**Key Methods**:
- `run(max_steps)`: Execute task until completion
- `step()`: Single iteration of the loop
- `get_next_action()`: Query LLM for next action
- `create_history_gif()`: Generate visual execution trace

**Configuration**:
- `task`: Natural language instruction
- `llm`: LangChain chat model instance
- `use_vision`: Enable screenshot processing
- `max_failures`: Retry limit for failed actions
- `validate_output`: Pydantic model for structured output

### 2. Browser Context (`browser_use/browser/context.py`)

**Responsibility**: Manages browser sessions and page state

**Key Features**:
- Playwright browser lifecycle management
- Network idle detection (`_wait_for_stable_network`)
- DOM extraction and element indexing
- Screenshot capture with coordinate mapping
- XPath to CSS selector conversion
- Cookie and session persistence

**Critical Methods**:
- `get_state()`: Snapshot current page (DOM + screenshot)
- `get_current_page()`: Access active Playwright page
- `execute_javascript()`: Run JS in browser context
- `take_screenshot()`: Capture full-page screenshots

### 3. Controller (`browser_use/controller/service.py`)

**Responsibility**: Action registry and execution engine

**Built-in Actions**:
- `go_to_url(url)`: Navigate to URL
- `search_google(query)`: Google search
- `click_element(index)`: Click indexed element
- `input_text(index, text)`: Type into element
- `scroll(direction)`: Scroll page
- `switch_tab(page_id)`: Switch browser tabs
- `done(text)`: Complete task with result

**Custom Actions**:
```python
@controller.registry.action('Description of action')
async def my_action(param: str, browser: BrowserContext):
	# Your implementation
	return ActionResult(extracted_content='result')
```

### 4. DOM Service (`browser_use/dom/service.py`)

**Responsibility**: Extract and process DOM structure

**Process**:
1. Execute `buildDomTree.js` in browser
2. Parse JavaScript response into Python objects
3. Build element index (selector_map)
4. Calculate coordinates and visibility
5. Track element changes via hashing

**Output**: `BrowserState` with:
- `element_tree`: Hierarchical DOM representation
- `selector_map`: {index: DOMElementNode}
- `screenshot`: Base64-encoded image
- `tabs`: Open tab information

### 5. Message Manager (`browser_use/agent/message_manager/service.py`)

**Responsibility**: Construct LLM prompts with context

**Features**:
- System prompt injection
- Token budget management
- Message history compaction
- Sensitive data masking
- Model-specific formatting (DeepSeek, reasoning models)

**Token Management**:
- Estimates tokens: `chars / 3 + images * 800`
- Cuts older messages when budget exceeded
- Preserves system prompt and recent context

---

## Usage Patterns

### Basic Usage

```python
from browser_use import Agent
from langchain_openai import ChatOpenAI


async def main():
	agent = Agent(
		task='Go to Amazon and find laptops under $1000',
		llm=ChatOpenAI(model='gpt-4o'),
	)
	result = await agent.run()
	print(result.final_result())


asyncio.run(main())
```

### Advanced Configuration

```python
from browser_use import Agent, Browser, BrowserConfig, Controller
from browser_use.agent.views import ActionResult

# Custom action
controller = Controller()


@controller.registry.action('Save data to file')
async def save_to_file(data: str, filename: str):
	with open(filename, 'w') as f:
		f.write(data)
	return ActionResult(extracted_content=f'Saved to {filename}')


# Custom browser config
browser = Browser(config=BrowserConfig(headless=False, disable_security=True, extra_chromium_args=['--start-maximized']))


# Structured output
class ProductList(BaseModel):
	products: List[str]
	prices: List[float]


controller_with_output = Controller(output_model=ProductList)

agent = Agent(
	task='Find 5 laptops and return names and prices',
	llm=ChatOpenAI(model='gpt-4o'),
	browser=browser,
	controller=controller_with_output,
	use_vision=True,
	max_failures=5,
	validate_output=True,
)

result = await agent.run(max_steps=50)
products = ProductList.model_validate_json(result.final_result())
```

### With Planning

```python
from browser_use import Agent
from browser_use.agent.prompts import SystemPrompt


class PlannerPrompt(SystemPrompt):
	def important_rules(self) -> str:
		return (
			super().important_rules()
			+ """

        ## Planning Rules
        - Break complex tasks into steps
        - Verify each step before proceeding
        - Document your reasoning
        """
		)


agent = Agent(
	task='Research and compare 3 cloud providers',
	llm=ChatOpenAI(model='gpt-4o'),
	system_prompt_class=PlannerPrompt,
	use_vision_for_planner=True,
)
```

---

## State Management

### Agent State

```python
AgentHistory:
  - model_output: AgentOutput      # LLM's decision
      - current_state: AgentBrain  # Reasoning snapshot
          - evaluation: str        # State assessment
          - memory: str            # Progress tracking
          - next_goal: str         # Immediate objective
      - action: List[ActionModel]  # Actions to execute
  - result: List[ActionResult]     # Execution results
  - state: BrowserState            # Browser snapshot post-action
```

### Browser State

```python
BrowserState:
  - url: str                       # Current URL
  - title: str                     # Page title
  - tabs: List[TabInfo]            # Open tabs
  - screenshot: str                # Base64 screenshot
  - element_tree: List[DOMNode]    # DOM hierarchy
  - selector_map: Dict[int, Node]  # Index to element mapping
```

---

## Error Handling

### Automatic Retries

The agent automatically retries failed actions up to `max_failures` times:
- LLM API rate limits
- Element not found errors
- Navigation timeouts
- JavaScript execution failures

### Error Recovery Strategies

1. **Element Not Found**: Re-extract DOM, search for similar elements
2. **Navigation Timeout**: Increase timeout, check network stability
3. **Action Failure**: Try alternative approaches (e.g., JS click vs Playwright click)
4. **Token Limit**: Compress message history, remove old context

### Custom Error Handling

```python
agent = Agent(
	task='...',
	llm=llm,
	max_failures=10,  # Increase retry limit
	retry_delay=5,  # Wait 5s between retries
)

try:
	result = await agent.run(max_steps=100)
except Exception as e:
	# Access partial history
	print(agent.history)
	# Save conversation for debugging
	agent.save_conversation('debug.json')
```

---

## Performance Optimization

### Token Usage

**Problem**: Large DOMs + screenshots consume tokens rapidly

**Solutions**:
1. Disable vision for simple tasks: `use_vision=False`
2. Set token budget: `max_input_tokens=50000`
3. Use smaller models for extraction: `small_model_for_extraction`
4. Compress history: Message manager auto-compacts

### Speed

**Problem**: Each step requires LLM round-trip

**Solutions**:
1. Use faster models: `gpt-4o-mini` vs `gpt-4o`
2. Reduce max steps: `max_steps=20`
3. Batch actions: `max_actions_per_step=5`
4. Use cached browser contexts

### Memory

**Problem**: Long runs accumulate browser state

**Solutions**:
1. Close unused tabs programmatically
2. Reset context periodically
3. Limit screenshot resolution
4. Use headless mode: `headless=True`

---

## Security Considerations

### Sensitive Data Masking

```python
agent = Agent(task='Login to example.com', llm=llm, sensitive_data={'password': 'my_secret_password', 'api_key': 'sk-...'})
# Replaces secrets in prompts with [REDACTED]
```

### Browser Security

```python
browser = Browser(
	config=BrowserConfig(
		disable_security=False,  # Keep security enabled
		chrome_instance_path=None,  # Don't reuse existing sessions
	)
)
```

### URL Restrictions

```python
from browser_use.browser.context import BrowserContextConfig

config = BrowserContextConfig(allowed_domains=['example.com', 'trusted-site.com'])
context = BrowserContext(browser=browser, config=config)
```

---

## Observability

### Telemetry

```python
# Telemetry auto-enabled via PostHog
# Tracks:
# - Task success/failure rates
# - Step counts
# - Error types
# - Model usage

# Disable:
import os

os.environ['ANONYMIZED_TELEMETRY'] = 'false'
```

### Conversation Logging

```python
agent = Agent(task='...', llm=llm, save_conversation_path='execution.json')

# Produces:
# {
#   "task": "...",
#   "history": [...],
#   "final_result": "..."
# }
```

### GIF Generation

```python
agent = Agent(task='...', llm=llm, generate_gif=True)
await agent.run()
agent.create_history_gif()  # Creates history.gif
```

---

## Testing

### Unit Testing

```python
from tests.utils import MockLLM, MockBrowserState


async def test_agent_step():
	mock_llm = MockLLM(responses=['{"action": [{"go_to_url": {"url": "https://example.com"}}]}'])

	agent = Agent(task='test', llm=mock_llm)
	await agent.step()

	assert mock_llm.call_count == 1
```

### Integration Testing

```python
@pytest.mark.integration
async def test_real_browser():
	agent = Agent(task='Go to example.com and get the title', llm=ChatOpenAI(model='gpt-4o-mini'))
	result = await agent.run(max_steps=5)
	assert 'Example' in result.final_result()
```

---

## Troubleshooting

### Issue: "Element with index X does not exist"

**Cause**: Selector indices change after page updates  
**Solution**: Re-extract DOM before clicking stale elements

### Issue: Token limit exceeded

**Cause**: Large pages + vision mode  
**Solution**: 
- Disable vision: `use_vision=False`
- Reduce history: `max_input_tokens=30000`

### Issue: Browser crashes

**Cause**: Memory exhaustion from screenshots  
**Solution**:
- Use headless mode
- Reduce screenshot quality
- Close unused tabs

### Issue: Actions timeout

**Cause**: Network instability or slow pages  
**Solution**:
- Increase retry delay: `retry_delay=10`
- Wait for network idle before extracting state

---

## Extension Points

### Custom Prompts

```python
from browser_use.agent.prompts import SystemPrompt


class CustomPrompt(SystemPrompt):
	def important_rules(self) -> str:
		return (
			super().important_rules()
			+ """

        ## Custom Rules
        - Always verify data before proceeding
        - Log reasoning at each step
        """
		)
```

### Custom Actions

See Controller section above.

### Custom DOM Processing

```python
from browser_use.dom.service import DomService


class CustomDomService(DomService):
	async def get_clickable_elements(self, page, viewport_expansion):
		# Override DOM extraction logic
		return custom_browser_state
```

---

## Performance Benchmarks

**Simple Navigation** (Go to URL):
- Steps: 1-2
- Time: 2-5 seconds
- Tokens: ~500

**Search Task** (Google search + click result):
- Steps: 3-5
- Time: 10-20 seconds
- Tokens: ~2,000

**Complex Task** (Multi-step workflow):
- Steps: 10-30
- Time: 1-5 minutes
- Tokens: ~20,000

**Shopping Task** (Find products, compare, add to cart):
- Steps: 15-40
- Time: 2-10 minutes
- Tokens: ~40,000

---

## Limitations

1. **Non-Deterministic**: LLM outputs vary, same task may produce different action sequences
2. **Cost**: Each step incurs LLM API costs (especially with vision)
3. **Speed**: Slower than direct Playwright scripts due to LLM reasoning overhead
4. **Complex UIs**: Struggles with SPAs, heavy JavaScript apps, CAPTCHAs
5. **Reliability**: ~80-90% success rate on well-defined tasks

---

## Best Practices

1. **Start Simple**: Test with simple tasks before complex workflows
2. **Use Vision Selectively**: Enable only when visual understanding needed
3. **Set Reasonable Limits**: `max_steps=50` prevents runaway execution
4. **Log Everything**: Use `save_conversation_path` for debugging
5. **Monitor Tokens**: Track costs with `tokencost` library
6. **Handle Failures**: Wrap `agent.run()` in try-except
7. **Test Incrementally**: Break complex tasks into smaller sub-tasks
8. **Validate Output**: Use `validate_output=True` with Pydantic models

---

## Resources

- **Documentation**: https://docs.browser-use.com
- **GitHub**: https://github.com/browser-use/browser-use
- **Discord**: https://link.browser-use.com/discord
- **Examples**: `/examples` directory (50+ examples)
- **API Reference**: See source code docstrings

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

---

**Last Updated**: 2026-05-31  
**Maintainers**: Gregor Zunic, Magnus Müller
