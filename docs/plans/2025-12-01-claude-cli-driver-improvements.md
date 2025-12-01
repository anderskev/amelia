# Claude CLI Driver Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance the Claude CLI driver to leverage the full capabilities of the Claude Code CLI including system prompts, model selection, permission management, timeout enforcement, and max turns control.

**Architecture:** The `ClaudeCliDriver` wraps the `claude` CLI binary using async subprocess execution. We will add configuration parameters to the constructor and build CLI arguments dynamically based on these settings. All changes maintain backward compatibility with existing callers.

**Tech Stack:** Python 3.12+, asyncio, Pydantic, pytest, pytest-asyncio

---

## Task 1: Add Model Selection Support

**Files:**
- Modify: `amelia/drivers/cli/claude.py:16-19` (constructor)
- Modify: `amelia/drivers/cli/claude.py:34-51` (`_generate_impl` command building)
- Modify: `amelia/drivers/factory.py:12-13` (pass model to constructor)
- Test: `tests/unit/test_claude_driver.py`

**Step 1: Write the failing test for model parameter**

Add to `tests/unit/test_claude_driver.py`:

```python
class TestClaudeCliDriverModelSelection:

    def test_default_model_is_sonnet(self):
        driver = ClaudeCliDriver()
        assert driver.model == "sonnet"

    def test_custom_model_parameter(self):
        driver = ClaudeCliDriver(model="opus")
        assert driver.model == "opus"

    @pytest.mark.asyncio
    async def test_model_flag_in_command(self, messages, mock_subprocess_process_factory):
        driver = ClaudeCliDriver(model="opus")
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages)

            args = mock_exec.call_args[0]
            assert "--model" in args
            model_idx = args.index("--model")
            assert args[model_idx + 1] == "opus"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverModelSelection -v`
Expected: FAIL with `AttributeError: 'ClaudeCliDriver' object has no attribute 'model'`

**Step 3: Add model parameter to constructor**

In `amelia/drivers/cli/claude.py`, modify the class:

```python
class ClaudeCliDriver(CliDriver):
    """
    Claude CLI Driver interacts with the Claude model via the local 'claude' CLI tool.
    """

    def __init__(
        self,
        model: str = "sonnet",
        timeout: int = 30,
        max_retries: int = 0,
    ):
        super().__init__(timeout, max_retries)
        self.model = model
```

**Step 4: Add model flag to command building**

In `amelia/drivers/cli/claude.py`, modify `_generate_impl`:

```python
async def _generate_impl(self, messages: list[AgentMessage], schema: type[BaseModel] | None = None) -> Any:
    """
    Generates a response using the 'claude' CLI.
    """
    full_prompt = self._convert_messages_to_prompt(messages)

    # Build the command
    # We use -p for print mode (non-interactive)
    cmd_args = ["claude", "-p", "--model", self.model]

    if schema:
        # ... rest unchanged
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverModelSelection -v`
Expected: PASS

**Step 6: Run full test suite to check for regressions**

Run: `uv run pytest tests/unit/test_claude_driver.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add amelia/drivers/cli/claude.py tests/unit/test_claude_driver.py
git commit -m "feat(cli-driver): add model selection support"
```

---

## Task 2: Add System Prompt Handling

**Files:**
- Modify: `amelia/drivers/cli/claude.py:21-32` (`_convert_messages_to_prompt`)
- Modify: `amelia/drivers/cli/claude.py:34-51` (`_generate_impl`)
- Test: `tests/unit/test_claude_driver.py`

**Step 1: Write the failing tests for system prompt handling**

Add to `tests/unit/test_claude_driver.py`:

```python
class TestClaudeCliDriverSystemPrompt:

    @pytest.fixture
    def messages_with_system(self):
        return [
            AgentMessage(role="system", content="You are a helpful assistant."),
            AgentMessage(role="user", content="Hello"),
            AgentMessage(role="assistant", content="Hi there"),
            AgentMessage(role="user", content="How are you?")
        ]

    def test_convert_messages_excludes_system(self, driver, messages_with_system):
        """System messages should not appear in the user prompt."""
        prompt = driver._convert_messages_to_prompt(messages_with_system)
        assert "SYSTEM:" not in prompt
        assert "You are a helpful assistant" not in prompt
        assert "USER: Hello" in prompt

    @pytest.mark.asyncio
    async def test_system_prompt_passed_via_flag(self, messages_with_system, mock_subprocess_process_factory):
        driver = ClaudeCliDriver()
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages_with_system)

            args = mock_exec.call_args[0]
            assert "--append-system-prompt" in args
            sys_idx = args.index("--append-system-prompt")
            assert args[sys_idx + 1] == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_multiple_system_messages_concatenated(self, mock_subprocess_process_factory):
        driver = ClaudeCliDriver()
        messages = [
            AgentMessage(role="system", content="Rule 1: Be helpful."),
            AgentMessage(role="system", content="Rule 2: Be concise."),
            AgentMessage(role="user", content="Hello"),
        ]
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages)

            args = mock_exec.call_args[0]
            sys_idx = args.index("--append-system-prompt")
            system_prompt = args[sys_idx + 1]
            assert "Rule 1: Be helpful." in system_prompt
            assert "Rule 2: Be concise." in system_prompt

    @pytest.mark.asyncio
    async def test_no_system_prompt_flag_when_no_system_messages(self, messages, mock_subprocess_process_factory):
        driver = ClaudeCliDriver()
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages)

            args = mock_exec.call_args[0]
            assert "--append-system-prompt" not in args
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverSystemPrompt -v`
Expected: FAIL

**Step 3: Modify `_convert_messages_to_prompt` to filter system messages**

In `amelia/drivers/cli/claude.py`:

```python
def _convert_messages_to_prompt(self, messages: list[AgentMessage]) -> str:
    """
    Converts a list of AgentMessages into a single string prompt.
    System messages are excluded as they are handled separately via CLI flags.
    """
    prompt_parts = []
    for msg in messages:
        if msg.role == "system":
            continue  # System messages handled separately
        role_str = msg.role.upper() if msg.role else "USER"
        content = msg.content or ""
        prompt_parts.append(f"{role_str}: {content}")

    # Join with newlines to create a transcript-like format
    return "\n\n".join(prompt_parts)
```

**Step 4: Modify `_generate_impl` to extract and pass system prompts**

In `amelia/drivers/cli/claude.py`:

```python
async def _generate_impl(self, messages: list[AgentMessage], schema: type[BaseModel] | None = None) -> Any:
    """
    Generates a response using the 'claude' CLI.
    """
    # Extract system messages
    system_messages = [m for m in messages if m.role == "system"]

    full_prompt = self._convert_messages_to_prompt(messages)

    # Build the command
    # We use -p for print mode (non-interactive)
    cmd_args = ["claude", "-p", "--model", self.model]

    # Add system prompt if present
    if system_messages:
        system_prompt = "\n\n".join(m.content for m in system_messages)
        cmd_args.extend(["--append-system-prompt", system_prompt])

    if schema:
        # Generate JSON schema
        json_schema = json.dumps(schema.model_json_schema())
        cmd_args.extend(["--json-schema", json_schema])
        cmd_args.extend(["--output-format", "json"])

    # ... rest unchanged from line 53 onwards
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverSystemPrompt -v`
Expected: PASS

**Step 6: Run full test suite**

Run: `uv run pytest tests/unit/test_claude_driver.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add amelia/drivers/cli/claude.py tests/unit/test_claude_driver.py
git commit -m "feat(cli-driver): add system prompt handling via --append-system-prompt"
```

---

## Task 3: Add Permission Management

**Files:**
- Modify: `amelia/drivers/cli/claude.py:16-30` (constructor)
- Modify: `amelia/drivers/cli/claude.py:34-60` (`_generate_impl`)
- Test: `tests/unit/test_claude_driver.py`

**Step 1: Write the failing tests for permission management**

Add to `tests/unit/test_claude_driver.py`:

```python
class TestClaudeCliDriverPermissions:

    def test_skip_permissions_default_false(self):
        driver = ClaudeCliDriver()
        assert driver.skip_permissions is False

    def test_skip_permissions_configurable(self):
        driver = ClaudeCliDriver(skip_permissions=True)
        assert driver.skip_permissions is True

    def test_allowed_tools_default_none(self):
        driver = ClaudeCliDriver()
        assert driver.allowed_tools is None

    def test_disallowed_tools_default_none(self):
        driver = ClaudeCliDriver()
        assert driver.disallowed_tools is None

    @pytest.mark.asyncio
    async def test_skip_permissions_flag_added(self, messages, mock_subprocess_process_factory):
        driver = ClaudeCliDriver(skip_permissions=True)
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages)

            args = mock_exec.call_args[0]
            assert "--dangerously-skip-permissions" in args

    @pytest.mark.asyncio
    async def test_skip_permissions_flag_not_added_when_false(self, messages, mock_subprocess_process_factory):
        driver = ClaudeCliDriver(skip_permissions=False)
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages)

            args = mock_exec.call_args[0]
            assert "--dangerously-skip-permissions" not in args

    @pytest.mark.asyncio
    async def test_allowed_tools_flag_added(self, messages, mock_subprocess_process_factory):
        driver = ClaudeCliDriver(allowed_tools=["Read", "Write", "Bash"])
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages)

            args = mock_exec.call_args[0]
            assert "--allowedTools" in args
            idx = args.index("--allowedTools")
            assert args[idx + 1] == "Read,Write,Bash"

    @pytest.mark.asyncio
    async def test_disallowed_tools_flag_added(self, messages, mock_subprocess_process_factory):
        driver = ClaudeCliDriver(disallowed_tools=["Bash"])
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages)

            args = mock_exec.call_args[0]
            assert "--disallowedTools" in args
            idx = args.index("--disallowedTools")
            assert args[idx + 1] == "Bash"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverPermissions -v`
Expected: FAIL with `AttributeError: 'ClaudeCliDriver' object has no attribute 'skip_permissions'`

**Step 3: Add permission parameters to constructor**

In `amelia/drivers/cli/claude.py`:

```python
class ClaudeCliDriver(CliDriver):
    """
    Claude CLI Driver interacts with the Claude model via the local 'claude' CLI tool.
    """

    def __init__(
        self,
        model: str = "sonnet",
        timeout: int = 30,
        max_retries: int = 0,
        skip_permissions: bool = False,
        allowed_tools: list[str] | None = None,
        disallowed_tools: list[str] | None = None,
    ):
        super().__init__(timeout, max_retries)
        self.model = model
        self.skip_permissions = skip_permissions
        self.allowed_tools = allowed_tools
        self.disallowed_tools = disallowed_tools
```

**Step 4: Add permission flags to command building**

In `amelia/drivers/cli/claude.py`, add after the model flag in `_generate_impl`:

```python
    # Build the command
    cmd_args = ["claude", "-p", "--model", self.model]

    # Add permission flags
    if self.skip_permissions:
        cmd_args.append("--dangerously-skip-permissions")
    if self.allowed_tools:
        cmd_args.extend(["--allowedTools", ",".join(self.allowed_tools)])
    if self.disallowed_tools:
        cmd_args.extend(["--disallowedTools", ",".join(self.disallowed_tools)])

    # Add system prompt if present
    # ... rest unchanged
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverPermissions -v`
Expected: PASS

**Step 6: Run full test suite**

Run: `uv run pytest tests/unit/test_claude_driver.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add amelia/drivers/cli/claude.py tests/unit/test_claude_driver.py
git commit -m "feat(cli-driver): add permission management (skip_permissions, allowed/disallowed tools)"
```

---

## Task 4: Add Timeout Enforcement

**Files:**
- Modify: `amelia/drivers/cli/claude.py:86-88` (subprocess wait)
- Test: `tests/unit/test_claude_driver.py`

**Step 1: Write the failing test for timeout enforcement**

Add to `tests/unit/test_claude_driver.py`:

```python
class TestClaudeCliDriverTimeout:

    @pytest.mark.asyncio
    async def test_timeout_kills_process(self, messages):
        driver = ClaudeCliDriver(timeout=1)

        # Create a process that hangs
        mock_process = AsyncMock()
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        # stdout.readline() hangs forever
        async def hang_forever():
            await asyncio.sleep(100)
            return b""
        mock_process.stdout.readline = hang_forever
        mock_process.stderr.read = AsyncMock(return_value=b"")
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process):
            with pytest.raises(RuntimeError, match="timed out"):
                await driver._generate_impl(messages)

            mock_process.kill.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverTimeout -v`
Expected: FAIL (test hangs or doesn't raise RuntimeError with "timed out")

**Step 3: Add timeout enforcement to subprocess execution**

In `amelia/drivers/cli/claude.py`, modify the gathering section:

```python
            # Run readers concurrently with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(read_stdout(), read_stderr()),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise RuntimeError(f"Claude CLI timed out after {self.timeout}s")

            await process.wait()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverTimeout -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `uv run pytest tests/unit/test_claude_driver.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add amelia/drivers/cli/claude.py tests/unit/test_claude_driver.py
git commit -m "feat(cli-driver): enforce timeout on subprocess execution"
```

---

## Task 5: Add Max Turns Control

**Files:**
- Modify: `amelia/drivers/cli/claude.py` (constructor and `_generate_impl`)
- Test: `tests/unit/test_claude_driver.py`

**Step 1: Write the failing tests for max turns**

Add to `tests/unit/test_claude_driver.py`:

```python
class TestClaudeCliDriverMaxTurns:

    def test_max_turns_default_none(self):
        driver = ClaudeCliDriver()
        assert driver.max_turns is None

    def test_max_turns_configurable(self):
        driver = ClaudeCliDriver(max_turns=5)
        assert driver.max_turns == 5

    @pytest.mark.asyncio
    async def test_max_turns_flag_added_when_set(self, messages, mock_subprocess_process_factory):
        driver = ClaudeCliDriver(max_turns=10)
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages)

            args = mock_exec.call_args[0]
            assert "--max-turns" in args
            idx = args.index("--max-turns")
            assert args[idx + 1] == "10"

    @pytest.mark.asyncio
    async def test_max_turns_flag_not_added_when_none(self, messages, mock_subprocess_process_factory):
        driver = ClaudeCliDriver(max_turns=None)
        mock_process = mock_subprocess_process_factory(
            stdout_lines=[b"response", b""],
            return_code=0
        )

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process) as mock_exec:
            await driver._generate_impl(messages)

            args = mock_exec.call_args[0]
            assert "--max-turns" not in args
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverMaxTurns -v`
Expected: FAIL with `AttributeError: 'ClaudeCliDriver' object has no attribute 'max_turns'`

**Step 3: Add max_turns parameter to constructor**

In `amelia/drivers/cli/claude.py`, update constructor:

```python
    def __init__(
        self,
        model: str = "sonnet",
        timeout: int = 30,
        max_retries: int = 0,
        skip_permissions: bool = False,
        allowed_tools: list[str] | None = None,
        disallowed_tools: list[str] | None = None,
        max_turns: int | None = None,
    ):
        super().__init__(timeout, max_retries)
        self.model = model
        self.skip_permissions = skip_permissions
        self.allowed_tools = allowed_tools
        self.disallowed_tools = disallowed_tools
        self.max_turns = max_turns
```

**Step 4: Add max_turns flag to command building**

In `amelia/drivers/cli/claude.py`, add after permission flags in `_generate_impl`:

```python
    # Add max turns if specified
    if self.max_turns is not None:
        cmd_args.extend(["--max-turns", str(self.max_turns)])
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_claude_driver.py::TestClaudeCliDriverMaxTurns -v`
Expected: PASS

**Step 6: Run full test suite**

Run: `uv run pytest tests/unit/test_claude_driver.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add amelia/drivers/cli/claude.py tests/unit/test_claude_driver.py
git commit -m "feat(cli-driver): add max_turns control for agentic loops"
```

---

## Task 6: Update DriverFactory to Support New Parameters

**Files:**
- Modify: `amelia/drivers/factory.py`
- Modify: `amelia/core/types.py` (if Profile needs new fields)
- Test: `tests/unit/test_driver_factory.py` (create if doesn't exist)

**Step 1: Write the failing test for factory with parameters**

Create or add to `tests/unit/test_driver_factory.py`:

```python
import pytest
from amelia.drivers.factory import DriverFactory
from amelia.drivers.cli.claude import ClaudeCliDriver


class TestDriverFactory:

    def test_cli_claude_default(self):
        driver = DriverFactory.get_driver("cli:claude")
        assert isinstance(driver, ClaudeCliDriver)
        assert driver.model == "sonnet"
        assert driver.skip_permissions is False

    def test_cli_claude_with_model(self):
        driver = DriverFactory.get_driver("cli:claude", model="opus")
        assert isinstance(driver, ClaudeCliDriver)
        assert driver.model == "opus"

    def test_cli_claude_with_permissions(self):
        driver = DriverFactory.get_driver("cli:claude", skip_permissions=True)
        assert isinstance(driver, ClaudeCliDriver)
        assert driver.skip_permissions is True

    def test_cli_claude_with_max_turns(self):
        driver = DriverFactory.get_driver("cli:claude", max_turns=5)
        assert isinstance(driver, ClaudeCliDriver)
        assert driver.max_turns == 5

    def test_unknown_driver_raises(self):
        with pytest.raises(ValueError, match="Unknown driver key"):
            DriverFactory.get_driver("unknown:driver")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_driver_factory.py -v`
Expected: FAIL with `TypeError: get_driver() got an unexpected keyword argument`

**Step 3: Update factory to accept kwargs**

In `amelia/drivers/factory.py`:

```python
from typing import Any

from amelia.drivers.api.openai import ApiDriver
from amelia.drivers.base import DriverInterface
from amelia.drivers.cli.claude import ClaudeCliDriver


class DriverFactory:
    @staticmethod
    def get_driver(driver_key: str, **kwargs: Any) -> DriverInterface:
        """
        Factory method to get a concrete driver implementation based on a key.

        Args:
            driver_key: Driver identifier (e.g., "cli:claude", "api:openai")
            **kwargs: Driver-specific configuration passed to constructor
        """
        if driver_key == "cli:claude" or driver_key == "cli":
            return ClaudeCliDriver(**kwargs)
        elif driver_key == "api:openai" or driver_key == "api":
            return ApiDriver(**kwargs)
        else:
            raise ValueError(f"Unknown driver key: {driver_key}")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_driver_factory.py -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add amelia/drivers/factory.py tests/unit/test_driver_factory.py
git commit -m "feat(factory): update DriverFactory to pass kwargs to driver constructors"
```

---

## Task 7: Run Full Verification and Lint

**Files:** None (verification only)

**Step 1: Run type checker**

Run: `uv run mypy amelia/drivers/`
Expected: No errors

**Step 2: Run linter**

Run: `uv run ruff check amelia/drivers/ tests/unit/test_claude_driver.py tests/unit/test_driver_factory.py`
Expected: No errors (or fix any that appear)

**Step 3: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All tests PASS

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "chore: fix lint/type issues from claude driver improvements"
```

---

## Summary

| Task | Description | Key Changes |
|------|-------------|-------------|
| 1 | Model Selection | Add `model` param, `--model` flag |
| 2 | System Prompt Handling | Extract system messages, use `--append-system-prompt` |
| 3 | Permission Management | Add `skip_permissions`, `allowed_tools`, `disallowed_tools` |
| 4 | Timeout Enforcement | Use `asyncio.wait_for`, kill on timeout |
| 5 | Max Turns Control | Add `max_turns` param, `--max-turns` flag |
| 6 | Factory Update | Pass kwargs through to driver constructors |
| 7 | Verification | mypy, ruff, pytest |

**Total estimated tasks:** 7 (each with 5-7 steps)

**Dependencies:** Tasks 1-5 can be done in any order. Task 6 depends on Tasks 1-5. Task 7 is always last.
