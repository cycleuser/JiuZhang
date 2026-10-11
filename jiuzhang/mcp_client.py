"""MCP Client & Tool Discovery — connect JiuZhang to external tool servers.

Model Context Protocol (MCP) support for:
- Wolfram Alpha, Lean theorem prover, SageMath, and other math tools
- MCP servers exposing computation, verification, and search capabilities
- Auto-discovery of tools from MCP servers
- Seamless integration with the tool registry

Inspired by nanobot's MCP tool integration.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import json
import asyncio
import subprocess
import os
from pathlib import Path


# ── MCP Tool Definition ──────────────────────────────────────────────

@dataclass
class MCPTool:
    """A tool exposed by an MCP server."""
    name: str
    description: str = ""
    server_name: str = ""
    parameters: dict = field(default_factory=dict)  # JSON Schema for parameters

    def to_function_schema(self) -> dict:
        """Convert to OpenAI function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def __repr__(self):
        return f"MCPTool({self.name}@{self.server_name})"


# ── MCP Server Config ────────────────────────────────────────────────

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str = ""           # Command to launch the server
    args: list[str] = field(default_factory=list)
    env: dict = field(default_factory=dict)
    url: str = ""               # URL for HTTP-based MCP servers
    description: str = ""       # Human-readable description
    auto_start: bool = True
    timeout: int = 30


# ── Built-in MCP Server Presets ──────────────────────────────────────

BUILTIN_MCP_SERVERS = {
    "wolfram-alpha": MCPServerConfig(
        name="wolfram-alpha",
        command="",
        url="https://api.wolframalpha.com/v1",
        description="Wolfram Alpha computational knowledge engine",
    ),
    "lean-prover": MCPServerConfig(
        name="lean-prover",
        command="lean", 
        args=["--server"],
        description="Lean theorem prover for formal verification",
    ),
    "sagemath": MCPServerConfig(
        name="sagemath",
        command="sage",
        args=["--mcp"],
        description="SageMath symbolic computation system",
    ),
}


# ── MCP Client ────────────────────────────────────────────────────────

class MCPClient:
    """Client for connecting to MCP (Model Context Protocol) servers.

    Supports:
    - Subprocess-based MCP servers (stdio transport)
    - HTTP-based MCP servers
    - Tool discovery and capability negotiation
    - Async tool execution with timeout
    """

    def __init__(self):
        self._servers: dict[str, MCPServerConfig] = {}
        self._tools: dict[str, MCPTool] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._connected: set[str] = set()

    def add_server(self, config: MCPServerConfig):
        self._servers[config.name] = config

    def add_builtin_servers(self):
        for name, config in BUILTIN_MCP_SERVERS.items():
            self._servers[name] = config

    async def connect_all(self):
        """Connect to all configured MCP servers."""
        for name, config in self._servers.items():
            try:
                await self.connect(name)
            except Exception as e:
                print(f"MCP: Failed to connect to {name}: {e}")

    async def connect(self, server_name: str) -> bool:
        """Connect to a specific MCP server and discover its tools."""
        if server_name in self._connected:
            return True

        config = self._servers.get(server_name)
        if not config:
            return False

        if config.url:
            # HTTP-based server
            self._connected.add(server_name)
            await self._discover_tools_http(server_name, config)
        elif config.command:
            # Subprocess-based server
            await self._start_subprocess(server_name, config)
            self._connected.add(server_name)
            await self._discover_tools_stdio(server_name, config)

        return server_name in self._connected

    async def disconnect(self, server_name: str):
        """Disconnect from an MCP server."""
        if server_name in self._processes:
            proc = self._processes.pop(server_name)
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()

        # Remove tools from this server
        self._tools = {
            k: v for k, v in self._tools.items()
            if v.server_name != server_name
        }
        self._connected.discard(server_name)

    async def call_tool(
        self, tool_name: str, arguments: dict, timeout: int = 30,
    ) -> dict:
        """Call a tool on an MCP server.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            timeout: Timeout in seconds

        Returns:
            Tool result dict
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return {"error": f"Unknown MCP tool: {tool_name}"}

        server_name = tool.server_name
        config = self._servers.get(server_name)

        if not config or server_name not in self._connected:
            return {"error": f"MCP server {server_name} not connected"}

        try:
            if config.url:
                result = await self._call_tool_http(server_name, tool_name, arguments, timeout)
            else:
                result = await self._call_tool_stdio(server_name, tool_name, arguments, timeout)

            return result
        except asyncio.TimeoutError:
            return {"error": f"Tool {tool_name} timed out after {timeout}s"}
        except Exception as e:
            return {"error": str(e)}

    async def _start_subprocess(self, server_name: str, config: MCPServerConfig):
        """Start an MCP server as a subprocess."""
        env = {**os.environ, **config.env}
        proc = await asyncio.create_subprocess_exec(
            config.command, *config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        self._processes[server_name] = proc

    async def _discover_tools_stdio(self, server_name: str, config: MCPServerConfig):
        """Discover tools from a stdio MCP server."""
        proc = self._processes.get(server_name)
        if not proc or not proc.stdin:
            return

        # Send initialize request (simplified MCP protocol)
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
        request_bytes = (json.dumps(init_request) + "\n").encode()
        proc.stdin.write(request_bytes)
        await proc.stdin.drain()

        try:
            response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=10)
            response = json.loads(response_line.decode())
            tools_data = response.get("result", {}).get("tools", [])
            for tool_data in tools_data:
                self._register_tool(server_name, tool_data)
        except (asyncio.TimeoutError, json.JSONDecodeError):
            # Server didn't respond — register placeholder tools
            pass

    async def _discover_tools_http(self, server_name: str, config: MCPServerConfig):
        """Discover tools from an HTTP MCP server."""
        # Placeholder for HTTP-based tool discovery
        # In production this would make HTTP requests to the server's /tools endpoint
        pass

    async def _call_tool_stdio(
        self, server_name: str, tool_name: str, arguments: dict, timeout: int,
    ) -> dict:
        """Call a tool via stdio MCP protocol."""
        proc = self._processes.get(server_name)
        if not proc or not proc.stdin:
            return {"error": f"Server {server_name} not running"}

        request = {
            "jsonrpc": "2.0",
            "id": int(asyncio.get_event_loop().time() * 1000),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        request_bytes = (json.dumps(request) + "\n").encode()
        proc.stdin.write(request_bytes)
        await proc.stdin.drain()

        try:
            response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout)
            response = json.loads(response_line.decode())
            if "error" in response:
                return {"error": response["error"]}
            return response.get("result", {})
        except asyncio.TimeoutError:
            return {"error": f"MCP call timed out after {timeout}s"}

    async def _call_tool_http(
        self, server_name: str, tool_name: str, arguments: dict, timeout: int,
    ) -> dict:
        """Call a tool via HTTP MCP protocol (placeholder)."""
        return {"error": "HTTP MCP not yet implemented"}

    def _register_tool(self, server_name: str, tool_data: dict):
        """Register a discovered tool."""
        tool = MCPTool(
            name=tool_data.get("name", f"{server_name}_unknown"),
            description=tool_data.get("description", ""),
            server_name=server_name,
            parameters=tool_data.get("inputSchema", {}),
        )
        self._tools[tool.name] = tool

    def get_tools(self) -> dict[str, MCPTool]:
        return dict(self._tools)

    def get_tool_schemas(self) -> list[dict]:
        """Get all tools as OpenAI function-calling schemas."""
        return [t.to_function_schema() for t in self._tools.values()]

    def list_servers(self) -> list[dict]:
        return [
            {
                "name": name,
                "connected": name in self._connected,
                "tools": len([t for t in self._tools.values() if t.server_name == name]),
            }
            for name in self._servers
        ]

    async def close(self):
        """Disconnect from all servers."""
        for name in list(self._connected):
            await self.disconnect(name)


# ── Tool Discovery & Auto-Registration ──────────────────────────────

class ToolDiscovery:
    """Auto-discover available tools from skills, MCP servers, and built-ins.

    Integrates with the tool registry to provide a unified tool interface.
    """

    def __init__(self, skill_manager=None, mcp_client=None):
        self._skill_manager = skill_manager
        self._mcp_client = mcp_client
        self._custom_tools: dict[str, dict] = {}

    def register_custom_tool(self, name: str, handler, schema: dict):
        """Register a custom tool function."""
        self._custom_tools[name] = {
            "handler": handler,
            "schema": schema,
        }

    def get_all_tool_schemas(self) -> list[dict]:
        """Get all available tool schemas for model context."""
        schemas = []

        # MCP tools
        if self._mcp_client:
            schemas.extend(self._mcp_client.get_tool_schemas())

        # Custom tools
        for name, info in self._custom_tools.items():
            schemas.append(info["schema"])

        # Built-in research tools
        schemas.extend(BUILTIN_TOOL_SCHEMAS)

        return schemas

    def get_tools_for_category(self, category: str) -> list[dict]:
        """Get tools filtered by category."""
        all_tools = self.get_all_tool_schemas()
        # Filter based on category (simplified)
        category_map = {
            "verify": ["sympy_compute", "verify_symbolic", "verify_equation", "lean_check", "wolfram_query"],
            "search": ["web_search", "search_arxiv", "oeis_lookup", "multi_search"],
            "compute": ["execute_code", "sympy_compute", "numeric_analyze"],
            "prove": ["prove_theorem", "lean_check", "verify_symbolic"],
        }
        allowed = set(category_map.get(category, []))
        if not allowed:
            return all_tools
        return [t for t in all_tools if t.get("function", {}).get("name", "") in allowed]


# ── Built-in Tool Schemas ───────────────────────────────────────────

BUILTIN_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "sympy_compute",
            "description": "Perform symbolic computation using SymPy: simplify, solve, integrate, differentiate, factor, expand, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "The SymPy expression to evaluate"},
                    "operation": {"type": "string", "enum": ["simplify", "solve", "integrate", "diff", "factor", "expand", "limit", "series"], "description": "The operation to perform"},
                    "variable": {"type": "string", "description": "The variable (for diff, integrate, limit)"},
                },
                "required": ["expression", "operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_equation",
            "description": "Verify if an equation is true using symbolic computation",
            "parameters": {
                "type": "object",
                "properties": {
                    "lhs": {"type": "string", "description": "Left-hand side of the equation"},
                    "rhs": {"type": "string", "description": "Right-hand side of the equation"},
                },
                "required": ["lhs", "rhs"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for mathematical references, definitions, and related work",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum number of results (default 5)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "oeis_lookup",
            "description": "Look up an integer sequence in the OEIS (Online Encyclopedia of Integer Sequences)",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {"type": "string", "description": "Comma-separated sequence of integers, e.g., '1,1,2,3,5,8'"},
                },
                "required": ["sequence"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Execute Python code in a sandboxed environment for numerical experiments",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 10)"},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_counterexample",
            "description": "Search for counterexamples to a mathematical claim by brute-force testing",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "The mathematical claim to test"},
                    "range_start": {"type": "integer", "description": "Start of search range"},
                    "range_end": {"type": "integer", "description": "End of search range (max 10000)"},
                },
                "required": ["claim"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "literature_search",
            "description": "Search academic literature (arXiv, CrossRef) for mathematical papers",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "source": {"type": "string", "enum": ["arxiv", "crossref", "all"], "description": "Source to search"},
                    "max_results": {"type": "integer", "description": "Maximum results (default 10)"},
                },
                "required": ["query"],
            },
        },
    },
]
