# Provider Auto-Inference Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate redundant provider specification in driver/model settings by passing provider from factory to driver.

**Architecture:** Extract provider from driver_key in factory and pass explicitly to ApiDriver. ApiDriver passes provider to `_create_chat_model()` instead of parsing model string.

**Tech Stack:** Python 3.12+, Pydantic, LangChain

---

## Task 1: Update `_create_chat_model` to Accept Provider Parameter

**Files:**
- Modify: `amelia/drivers/api/deepagents.py:106-154`
- Test: `tests/unit/test_api_driver.py`

**Step 1: Write the failing test for provider parameter**

Add test in `tests/unit/test_api_driver.py` in `TestCreateChatModel`:

```python
def test_openrouter_provider_without_prefix(self) -> None:
    """Should configure OpenRouter when provider param is 'openrouter' (no model prefix)."""
    with (
        patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-api-key"}),
        patch("amelia.drivers.api.deepagents.init_chat_model") as mock_init,
    ):
        mock_init.return_value = MagicMock()

        _create_chat_model("minimax/minimax-m2", provider="openrouter")

        mock_init.assert_called_once_with(
            model="minimax/minimax-m2",
            model_provider="openai",
            base_url="https://openrouter.ai/api/v1",
            api_key="test-api-key",
            default_headers={
                "HTTP-Referer": "https://github.com/existential-birds/amelia",
                "X-Title": "Amelia",
            },
        )
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_api_driver.py::TestCreateChatModel::test_openrouter_provider_without_prefix -v`
Expected: FAIL with TypeError about unexpected `provider` argument

**Step 3: Update `_create_chat_model` signature and implementation**

Modify `amelia/drivers/api/deepagents.py:106-154`. Replace the function:

```python
def _create_chat_model(model: str, provider: str | None = None) -> BaseChatModel:
    """Create a LangChain chat model, handling provider configuration.

    Provider can be specified explicitly via parameter, or legacy 'openrouter:' prefix.

    Args:
        model: Model identifier (e.g., 'minimax/minimax-m2' or legacy 'openrouter:minimax/minimax-m2').
        provider: Optional provider name. If 'openrouter', configures OpenRouter API.

    Returns:
        Configured BaseChatModel instance.

    Raises:
        ValueError: If OpenRouter is requested but OPENROUTER_API_KEY is not set.
    """
    # Handle legacy prefix format for backwards compatibility during transition
    if model.startswith("openrouter:"):
        model = model[len("openrouter:"):]
        provider = "openrouter"

    if provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required for OpenRouter models"
            )

        site_url = os.environ.get(
            "OPENROUTER_SITE_URL", "https://github.com/existential-birds/amelia"
        )
        site_name = os.environ.get("OPENROUTER_SITE_NAME", "Amelia")

        return init_chat_model(
            model=model,
            model_provider="openai",
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": site_url,
                "X-Title": site_name,
            },
        )

    return init_chat_model(model)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_api_driver.py::TestCreateChatModel::test_openrouter_provider_without_prefix -v`
Expected: PASS

**Step 5: Run all `_create_chat_model` tests to ensure no regressions**

Run: `uv run pytest tests/unit/test_api_driver.py::TestCreateChatModel -v`
Expected: All PASS (legacy prefix tests still work)

**Step 6: Commit**

```bash
git add amelia/drivers/api/deepagents.py tests/unit/test_api_driver.py
git commit -m "feat(drivers): add provider param to _create_chat_model"
```

---

## Task 2: Add Provider Parameter to ApiDriver

**Files:**
- Modify: `amelia/drivers/api/deepagents.py:157-179`
- Test: `tests/unit/test_api_driver.py`

**Step 1: Write the failing test for provider parameter in ApiDriver**

Add test in `tests/unit/test_api_driver.py` in `TestApiDriverInit`:

```python
def test_stores_provider(self) -> None:
    """Should store the provider parameter."""
    driver = ApiDriver(provider="openrouter")
    assert driver.provider == "openrouter"

def test_provider_defaults_to_openrouter(self) -> None:
    """Should default provider to 'openrouter' when not specified."""
    driver = ApiDriver()
    assert driver.provider == "openrouter"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_api_driver.py::TestApiDriverInit::test_stores_provider tests/unit/test_api_driver.py::TestApiDriverInit::test_provider_defaults_to_openrouter -v`
Expected: FAIL with AttributeError

**Step 3: Update ApiDriver `__init__` to accept and store provider**

Modify `amelia/drivers/api/deepagents.py:157-179`. Update the class:

```python
class ApiDriver(DriverInterface):
    """DeepAgents-based driver for LLM generation and agentic execution.

    Uses LangGraph-based autonomous agent via the deepagents library.
    Supports any model available through langchain's init_chat_model.

    Attributes:
        model: The model identifier (e.g., 'minimax/minimax-m2').
        provider: The provider name (e.g., 'openrouter').
        cwd: Working directory for agentic execution.
    """

    DEFAULT_MODEL = "minimax/minimax-m2"

    def __init__(
        self,
        model: str | None = None,
        cwd: str | None = None,
        provider: str = "openrouter",
    ):
        """Initialize the API driver.

        Args:
            model: Model identifier for langchain (e.g., 'minimax/minimax-m2').
            cwd: Working directory for agentic execution. Required for execute_agentic().
            provider: Provider name (e.g., 'openrouter'). Defaults to 'openrouter'.
        """
        self.model = model or self.DEFAULT_MODEL
        self.provider = provider
        self.cwd = cwd
        self._usage: DriverUsage | None = None
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_api_driver.py::TestApiDriverInit::test_stores_provider tests/unit/test_api_driver.py::TestApiDriverInit::test_provider_defaults_to_openrouter -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/drivers/api/deepagents.py tests/unit/test_api_driver.py
git commit -m "feat(drivers): add provider param to ApiDriver"
```

---

## Task 3: Wire Provider Through ApiDriver Methods

**Files:**
- Modify: `amelia/drivers/api/deepagents.py:181-284` (generate method)
- Modify: `amelia/drivers/api/deepagents.py:286-458` (execute_agentic method)
- Test: `tests/unit/test_api_driver.py`

**Step 1: Write failing test for generate() using provider**

Add test in `tests/unit/test_api_driver.py` in `TestGenerate`:

```python
async def test_passes_provider_to_create_chat_model(
    self, mock_deepagents: MagicMock
) -> None:
    """Should pass provider to _create_chat_model."""
    driver = ApiDriver(model="test/model", cwd="/test", provider="openrouter")
    mock_deepagents.agent_result["messages"] = [AIMessage(content="response")]

    with patch("amelia.drivers.api.deepagents._create_chat_model") as mock_create:
        mock_create.return_value = MagicMock()
        await driver.generate(prompt="test")

        mock_create.assert_called_once_with("test/model", provider="openrouter")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_api_driver.py::TestGenerate::test_passes_provider_to_create_chat_model -v`
Expected: FAIL (provider not passed)

**Step 3: Update generate() to pass provider**

In `amelia/drivers/api/deepagents.py`, modify the `generate` method line ~209:

Change:
```python
chat_model = _create_chat_model(self.model)
```

To:
```python
chat_model = _create_chat_model(self.model, provider=self.provider)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_api_driver.py::TestGenerate::test_passes_provider_to_create_chat_model -v`
Expected: PASS

**Step 5: Write failing test for execute_agentic() using provider**

Add test in `tests/unit/test_api_driver.py` in `TestExecuteAgentic`:

```python
async def test_passes_provider_to_create_chat_model(
    self, mock_deepagents: MagicMock
) -> None:
    """Should pass provider to _create_chat_model in execute_agentic."""
    driver = ApiDriver(model="test/model", cwd="/test", provider="openrouter")
    mock_deepagents.stream_chunks = [
        {"messages": [AIMessage(content="done")]},
    ]

    with patch("amelia.drivers.api.deepagents._create_chat_model") as mock_create:
        mock_create.return_value = MagicMock()
        async for _ in driver.execute_agentic(prompt="test", cwd="/test"):
            pass

        mock_create.assert_called_once_with("test/model", provider="openrouter")
```

**Step 6: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_api_driver.py::TestExecuteAgentic::test_passes_provider_to_create_chat_model -v`
Expected: FAIL (provider not passed)

**Step 7: Update execute_agentic() to pass provider**

In `amelia/drivers/api/deepagents.py`, modify the `execute_agentic` method line ~326:

Change:
```python
chat_model = _create_chat_model(self.model)
```

To:
```python
chat_model = _create_chat_model(self.model, provider=self.provider)
```

**Step 8: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_api_driver.py::TestExecuteAgentic::test_passes_provider_to_create_chat_model -v`
Expected: PASS

**Step 9: Run all ApiDriver tests to verify no regressions**

Run: `uv run pytest tests/unit/test_api_driver.py -v`
Expected: All PASS

**Step 10: Commit**

```bash
git add amelia/drivers/api/deepagents.py tests/unit/test_api_driver.py
git commit -m "feat(drivers): wire provider through ApiDriver methods"
```

---

## Task 4: Update Factory to Pass Provider to ApiDriver

**Files:**
- Modify: `amelia/drivers/factory.py:21-26`
- Test: `tests/unit/test_driver_factory.py`

**Step 1: Write failing test for factory passing provider**

Add test in `tests/unit/test_driver_factory.py` in `TestDriverFactory`:

```python
def test_api_openrouter_passes_provider(self) -> None:
    """Factory should pass provider='openrouter' to ApiDriver for api:openrouter."""
    driver = DriverFactory.get_driver("api:openrouter")
    assert isinstance(driver, ApiDriver)
    assert driver.provider == "openrouter"

def test_api_shorthand_passes_provider(self) -> None:
    """Factory should pass provider='openrouter' to ApiDriver for 'api' shorthand."""
    driver = DriverFactory.get_driver("api")
    assert isinstance(driver, ApiDriver)
    assert driver.provider == "openrouter"
```

**Step 2: Run tests to verify they pass (provider already defaults)**

Run: `uv run pytest tests/unit/test_driver_factory.py::TestDriverFactory::test_api_openrouter_passes_provider tests/unit/test_driver_factory.py::TestDriverFactory::test_api_shorthand_passes_provider -v`
Expected: PASS (provider defaults to 'openrouter' in ApiDriver)

**Step 3: Make factory explicitly pass provider for clarity**

Modify `amelia/drivers/factory.py:21-26`:

Change:
```python
elif driver_key in ("api:openrouter", "api"):
    return ApiDriver(**kwargs)
```

To:
```python
elif driver_key in ("api:openrouter", "api"):
    return ApiDriver(provider="openrouter", **kwargs)
```

**Step 4: Run all factory tests to verify no regressions**

Run: `uv run pytest tests/unit/test_driver_factory.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add amelia/drivers/factory.py tests/unit/test_driver_factory.py
git commit -m "feat(drivers): factory explicitly passes provider to ApiDriver"
```

---

## Task 5: Update DEFAULT_MODEL to Remove Prefix

**Files:**
- Modify: `amelia/drivers/api/deepagents.py:168`
- Test: `tests/unit/test_api_driver.py`

**Step 1: Update test expectation for default model**

Modify `tests/unit/test_api_driver.py` in `TestApiDriverInit::test_defaults_to_minimax_m2`:

```python
def test_defaults_to_minimax_m2(self) -> None:
    """Should default to MiniMax M2 when no model provided."""
    driver = ApiDriver()
    assert driver.model == ApiDriver.DEFAULT_MODEL
    assert driver.model == "minimax/minimax-m2"  # No prefix
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_api_driver.py::TestApiDriverInit::test_defaults_to_minimax_m2 -v`
Expected: FAIL (current default has 'openrouter:' prefix)

**Step 3: Update DEFAULT_MODEL**

Modify `amelia/drivers/api/deepagents.py:168`:

Change:
```python
DEFAULT_MODEL = "openrouter:minimax/minimax-m2"
```

To:
```python
DEFAULT_MODEL = "minimax/minimax-m2"
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_api_driver.py::TestApiDriverInit::test_defaults_to_minimax_m2 -v`
Expected: PASS

**Step 5: Commit**

```bash
git add amelia/drivers/api/deepagents.py tests/unit/test_api_driver.py
git commit -m "feat(drivers): remove openrouter prefix from DEFAULT_MODEL"
```

---

## Task 6: Update Profile.model Docstring

**Files:**
- Modify: `amelia/core/types.py:46-48`

**Step 1: Update docstring**

Modify `amelia/core/types.py:46-48`:

Change:
```python
model: LLM model identifier. For cli:claude use 'sonnet', 'opus', or 'haiku'.
    For api:openrouter use 'provider:model' format (e.g., 'anthropic/claude-3.5-sonnet').
```

To:
```python
model: LLM model identifier. For cli:claude use 'sonnet', 'opus', or 'haiku'.
    For api:openrouter use model name directly (e.g., 'minimax/minimax-m2').
    The provider is inferred from the driver setting.
```

**Step 2: Run type check to ensure no issues**

Run: `uv run mypy amelia/core/types.py`
Expected: Success, no errors

**Step 3: Commit**

```bash
git add amelia/core/types.py
git commit -m "docs(types): update Profile.model docstring for provider inference"
```

---

## Task 7: Update Test Fixtures to Remove Prefix

**Files:**
- Modify: `tests/conftest.py:157-158`
- Modify: `tests/unit/test_driver_factory.py:18`
- Modify: `tests/unit/test_api_driver.py:28,36`

**Step 1: Update conftest.py api_single preset**

Modify `tests/conftest.py:157-158`:

Change:
```python
elif preset == "api_single":
    return Profile(name="test_api", driver="api:openrouter", model="anthropic/claude-3.5-sonnet", tracker="noop", strategy="single", **kwargs)
elif preset == "api_competitive":
    return Profile(name="test_comp", driver="api:openrouter", model="anthropic/claude-3.5-sonnet", tracker="noop", strategy="competitive", **kwargs)
```

To:
```python
elif preset == "api_single":
    return Profile(name="test_api", driver="api:openrouter", model="anthropic/claude-sonnet-4-20250514", tracker="noop", strategy="single", **kwargs)
elif preset == "api_competitive":
    return Profile(name="test_comp", driver="api:openrouter", model="anthropic/claude-sonnet-4-20250514", tracker="noop", strategy="competitive", **kwargs)
```

**Step 2: Update test_driver_factory.py parametrized test**

Modify `tests/unit/test_driver_factory.py:18`:

Change:
```python
("api:openrouter", ApiDriver, "openrouter:anthropic/claude-sonnet-4-20250514", "openrouter:anthropic/claude-sonnet-4-20250514"),
```

To:
```python
("api:openrouter", ApiDriver, "anthropic/claude-sonnet-4-20250514", "anthropic/claude-sonnet-4-20250514"),
```

**Step 3: Update test_api_driver.py fixture and test**

Modify `tests/unit/test_api_driver.py:28`:

Change:
```python
return ApiDriver(model="openrouter:test/model", cwd="/test/path")
```

To:
```python
return ApiDriver(model="test/model", cwd="/test/path", provider="openrouter")
```

Modify `tests/unit/test_api_driver.py:36`:

Change:
```python
driver = ApiDriver(model="openrouter:anthropic/claude-sonnet-4-20250514")
assert driver.model == "openrouter:anthropic/claude-sonnet-4-20250514"
```

To:
```python
driver = ApiDriver(model="anthropic/claude-sonnet-4-20250514", provider="openrouter")
assert driver.model == "anthropic/claude-sonnet-4-20250514"
```

**Step 4: Run all tests to verify no regressions**

Run: `uv run pytest tests/unit/test_driver_factory.py tests/unit/test_api_driver.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/conftest.py tests/unit/test_driver_factory.py tests/unit/test_api_driver.py
git commit -m "test: update fixtures to use clean model names without prefix"
```

---

## Task 8: Run Full Test Suite and Type Check

**Files:**
- None (verification only)

**Step 1: Run ruff linter**

Run: `uv run ruff check amelia tests`
Expected: No errors

**Step 2: Run mypy type check**

Run: `uv run mypy amelia`
Expected: Success, no errors

**Step 3: Run full test suite**

Run: `uv run pytest`
Expected: All tests pass

**Step 4: Commit any fixes if needed**

If any fixes are needed, commit them with appropriate messages.

---

## Task 9: Final Cleanup and Squash Commits (Optional)

**Files:**
- None (git operations only)

**Step 1: Review commit history**

Run: `git log --oneline -10`

**Step 2: Interactive rebase to squash if desired (user decision)**

If the user wants a single commit:
```bash
git rebase -i HEAD~8
```

Otherwise, keep the granular commits for better git history.
