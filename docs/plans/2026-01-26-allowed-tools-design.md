# Allowed Tools: Driver-Level Tool Filtering

**Date:** 2026-01-26
**Status:** Accepted
**Area:** Core / Drivers

## Problem

Oracle (a read-only consulting agent) needs to run with restricted tool access — only read/search tools, no writes or shell execution. Neither driver currently supports tool filtering. The CLI driver passes `bypass_permissions=True` with no restrictions. The API driver accepts a `tools` kwarg for DeepAgents tool objects, but nobody uses it.

## Design

Add `allowed_tools: list[str] | None` to the `DriverInterface.execute_agentic()` signature. When `None` (default), all tools are available. When set, only the listed tools may be used.

Both drivers accept the same canonical tool name strings (e.g., `read_file`, `glob`, `grep`). Each driver maps these to its native representation internally.

### Canonical Tool Names

All tools get canonical names in `ToolName` enum (`amelia/core/constants.py`):

| Canonical Name | CLI SDK Name | Category |
|----------------|-------------|----------|
| `read_file` | `Read` | File ops |
| `write_file` | `Write` | File ops |
| `edit_file` | `Edit` | File ops |
| `notebook_edit` | `NotebookEdit` | File ops |
| `glob` | `Glob` | File ops |
| `grep` | `Grep` | File ops |
| `run_shell_command` | `Bash` | Execution |
| `task` | `Task` | Agent orchestration |
| `task_output` | `TaskOutput` | Agent orchestration |
| `task_stop` | `TaskStop` | Agent orchestration |
| `enter_plan_mode` | `EnterPlanMode` | Planning |
| `exit_plan_mode` | `ExitPlanMode` | Planning |
| `ask_user_question` | `AskUserQuestion` | Interaction |
| `skill` | `Skill` | Interaction |
| `task_create` | `TaskCreate` | Task tracking |
| `task_get` | `TaskGet` | Task tracking |
| `task_update` | `TaskUpdate` | Task tracking |
| `task_list` | `TaskList` | Task tracking |
| `web_fetch` | `WebFetch` | Web |
| `web_search` | `WebSearch` | Web |

### Bidirectional Mapping

- `TOOL_NAME_ALIASES` (existing, expanded): CLI SDK name → canonical. Used when normalizing tool names in event streams.
- `CANONICAL_TO_CLI` (new): canonical → CLI SDK name. Derived by inverting `TOOL_NAME_ALIASES`. Used when passing `allowed_tools` to the CLI SDK.

### Presets

Named constants for common tool sets:

```python
READONLY_TOOLS: list[str] = [
    ToolName.READ_FILE,
    ToolName.GLOB,
    ToolName.GREP,
    ToolName.TASK,
    ToolName.TASK_OUTPUT,
    ToolName.WEB_FETCH,
    ToolName.WEB_SEARCH,
]
```

### Interface Change

`DriverInterface.execute_agentic()` in `amelia/drivers/base.py`:

```python
def execute_agentic(
    self,
    prompt: str,
    cwd: str,
    session_id: str | None = None,
    instructions: str | None = None,
    schema: type[BaseModel] | None = None,
    allowed_tools: list[str] | None = None,
    **kwargs: Any,
) -> AsyncIterator["AgenticMessage"]:
```

### CLI Driver Implementation

`ClaudeCliDriver` in `amelia/drivers/cli/claude.py`:

1. `execute_agentic()` accepts `allowed_tools` and passes it to `_build_options()`.
2. `_build_options()` maps canonical names to CLI SDK names via `CANONICAL_TO_CLI`.
3. The mapped list is passed to `ClaudeAgentOptions(allowed_tools=...)`.
4. Unknown canonical names (no CLI mapping) are skipped with a debug log.
5. When `allowed_tools is None`, the parameter is omitted from `ClaudeAgentOptions`, preserving current behavior.

The Claude Agent SDK natively supports `allowed_tools: list[str]` on `ClaudeAgentOptions`, so no hooks or workarounds are needed.

### API Driver — Stub Only

`ApiDriver` in `amelia/drivers/api/deepagents.py`:

The signature is updated to accept `allowed_tools`, but passing a non-None value raises `NotImplementedError`.

DeepAgents injects default tools via `FilesystemMiddleware` internally within `create_deep_agent()`. Filtering requires either custom middleware or manual agent construction. Since Oracle uses the CLI driver, this is deferred until a concrete need arises.

## Scope

### In Scope

- `ToolName` enum with all 20 CLI tools
- Bidirectional name mapping (`TOOL_NAME_ALIASES` expanded, `CANONICAL_TO_CLI` added)
- `READONLY_TOOLS` preset
- `allowed_tools` parameter on `DriverInterface.execute_agentic()`
- CLI driver: full implementation mapping canonical → CLI SDK names
- API driver: signature updated, `NotImplementedError` when used

### Out of Scope

- `disallowed_tools` (blacklist) — YAGNI
- API driver tool filtering implementation — deferred
- Additional presets beyond `READONLY_TOOLS` — add when needed
- Oracle agent implementation — separate work
