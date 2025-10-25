# ToolFabric for Google ADK

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, YAML-driven framework for managing and attaching enterprise-ready tools to Google Agent Development Kit (ADK) agents. Supports MCP (Message Control Protocol) clients with health checks, internal Python functions, and subprocess-based tools. Designed for dynamic LLM orchestration in production environments.

## Features

- **YAML Configuration**: Define tools declaratively with commands, modules, health checks, and multi-protocol MCP clients.
- **Tool Types**:
  - **MCP-Based Tools**: Launch external processes (e.g., Playwright MCP server) and route actions via MCP clients.
  - **Internal Python Tools**: Wrap reusable functions (e.g., user info retrieval) as ADK-compatible tools.
- **Health Monitoring**: Automatic periodic checks (ping/internal) with auto-reconnect for MCP clients.
- **Multi-Client Support**: Attach multiple MCP clients per tool (e.g., stdio, SSE) with independent protocols and health.
- **Seamless ADK Integration**: Load tools once and attach to any ADK `Agent` instance.
- **Thread-Safe & Robust**: Logging, validation, error handling, and graceful shutdowns.
- **No Hot-Add/Remove**: Simplified for static setups—load from YAML and attach to agent.

## Project Structure

Updated structure to consolidate all reusable Python modules into a dedicated `src/` folder for better modularity and packaging potential. Examples remain isolated.

```
toolfabric-adk/
├── README.md                 # This file
├── src/                      # Reusable core modules
│   ├── __init__.py          # Makes src installable as package
│   ├── mcp_client.py        # MCP client with protocol handlers
│   ├── base_tool.py         # Abstract base for tools
│   ├── tool_factory.py      # Creates tool instances from config
│   ├── tool_fabric.py       # Orchestrates loading and attachment
│   └── tools/               # Tool subclasses
│       ├── __init__.py
│       ├── internal_function_tool.py
│       └── mcp_based_tool.py
├── enterprise_tools/         # Domain-specific internal tool modules (e.g., user utils)
│   └── user.py              # Stub internal tool module
└── examples/                # Usage demos and stubs
    ├── config.yml           # Sample YAML config
    ├── run_adk_agent.py     # Usage example
    └── local_server.py      # Stub for subprocess testing
```

## Requirements

- Python 3.8+
- `pyyaml` (for YAML parsing): `pip install pyyaml`
- Optional: Real ADK (`pip install google-adk` or equivalent—stubbed in examples)
- For MCP protocols: Add libs like `websockets` or `requests` as needed (stubs provided).

No internet access required during runtime; stubs simulate connections.

## Installation

1. Clone or download the repo:
   ```
   git clone <repo-url>
   cd toolfabric-adk
   ```

2. Install dependencies:
   ```
   pip install pyyaml
   ```

3. (Optional) Install as package (for larger projects):
   ```
   pip install -e .
   ```
   (Requires `setup.py`—add if needed: `from setuptools import setup; setup(name='toolfabric', packages=['src'])`)

4. For real ADK integration: Install Google ADK SDK per [official docs](https://cloud.google.com/agent-development-kit/docs).

5. Create stubs if needed:
   - `enterprise_tools/user.py`: Provided in code snippets.
   - `examples/local_server.py`: Simple loop script for testing subprocess tools:
     ```python
     import time
     print("Local server running")
     while True:
         time.sleep(1)
     ```

## Configuration

Tools are defined in YAML. Key sections:

- `name`: Unique tool ID.
- `command`: For subprocess tools (list of args).
- `module` / `function`: For internal Python tools.
- `health_check`: `{type: "ping"|"internal", interval: seconds}`.
- `mcp_clients`: Array of clients with `name`, `host`, `port`, `protocol` ("stdio"|"sse"), `enabled`.

### Example `examples/config.yml`

```yaml
tools:
  - name: "playwright"
    command: ["npx", "@playwright/mcp@latest", "--headless"]
    health_check:
      type: "ping"
      interval: 5
    mcp_clients:
      - name: "playwright-client-1"
        host: "localhost"
        port: 8081
        protocol: "stdio"
        enabled: true

  - name: "local_server"
    command: ["python", "local_server.py"]
    health_check:
      type: "ping"
      interval: 10
    mcp_clients:
      - name: "local-client"
        host: "localhost"
        port: 9090
        protocol: "sse"
        enabled: true

  - name: "user_info"
    module: "enterprise_tools.user"
    function: "get_userInfo"
    health_check:
      type: "internal"
      interval: 30
    mcp_clients:
      - name: "user-logger"
        host: "logs.local"
        port: 8000
        protocol: "sse"
        enabled: true
```

## Usage

1. **Load and Attach Tools**:
   Use `ToolFabric` to parse YAML, start tools, and attach to an ADK agent. Imports now reference the `src/` package.

   ```python
   from src.tool_fabric import ToolFabric
   from google import adk  # Real import

   # Load config
   fabric = ToolFabric("examples/config.yml")
   tools = fabric.setup()  # Starts tools and health checks

   # Create ADK Agent
   agent = adk.Agent(name="MyAgent", description="Tool-enabled agent")

   # Attach all tools
   fabric.attach_all_to_agent(agent)

   # Now agent.tools["user_info"](user_id=123) works!
   result = agent.tools["user_info"](user_id=123)
   print(result)  # {"user_id": 123, "name": "John Doe", "role": "admin"}
   ```

2. **Run the Example**:
   ```
   cd examples
   python run_adk_agent.py
   ```
   - Outputs: Tool loading, attachment list, sample tool call.
   - Uses stub `StubADKAgent`—replace with real `adk.Agent`.

3. **Teardown**:
   Call `fabric.stop_all()` to disconnect clients and terminate processes.

## Logging

Uses Python's `logging` module. Configure via:
```python
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

## Extending

- **New Tool Type**: Add a subclass of `BaseTool` in `src/tools/` and register in `src/tool_factory.py`.
- **Protocol Handler**: Implement `ProtocolHandler` subclass in `src/mcp_client.py` (e.g., WebSocket).
- **Custom Health**: Override `_health_check_internal` in tool classes.
- **Domain Modules**: Add more to `enterprise_tools/` for internal functions.

## Testing

- Run `run_adk_agent.py` for integration test.
- Unit tests: Add via `pytest` (not included—focus on stubs for now).

## Limitations & Notes

- MCP handlers are stubs—implement real connections (e.g., via `subprocess` pipes or `requests`).
- Assumes ADK `Agent` has `attach_tool(name, func)` or `tools` dict.
- No async support yet—synchronous for simplicity.
- For production: Add metrics (Prometheus), secrets (env vars), and full validation (Pydantic).

## Contributing

Fork, PR with tests. Issues welcome!

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*Built for enterprise LLM agents. Questions? Open an issue.*

### Migration Notes (from Previous Structure)
- Moved `mcp_client.py`, `base_tool.py`, `tool_factory.py`, `tool_fabric.py`, and `tools/` to `src/`.
- Added `__init__.py` files for package structure.
- Updated imports in affected files:
  - In `src/tool_factory.py`: `from .tools.internal_function_tool import InternalFunctionTool` (relative imports).
  - In `src/tools/internal_function_tool.py` and `mcp_based_tool.py`: `from ..base_tool import BaseTool`.
  - In `examples/run_adk_agent.py`: `from src.tool_fabric import ToolFabric`.
- `enterprise_tools/` remains outside `src/` as it's domain-specific (not core reusable).
- No changes to YAML or stubs needed.
- To run: Ensure Python path includes `src/` (or install as editable package).

If you need the full updated code files (e.g., with import fixes), let me know!
