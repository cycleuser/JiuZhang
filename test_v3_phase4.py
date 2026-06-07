"""Phase 4 unit tests — Skills System, MCP Client, Tool Discovery."""
import os, subprocess, sys

PYTHON = "/Users/fred/miniconda3/bin/python"
ROOT = "/Users/fred/Documents/GitHub/cycleuser/JiuZhang"
ENV = {**os.environ, "PYTHONPATH": ROOT}


def T(name, script):
    global ok, total
    total += 1
    r = subprocess.run([PYTHON, "-c", script], capture_output=True, text=True, timeout=60, cwd=ROOT, env=ENV)
    if r.returncode == 0:
        print(f"OK {name}")
        ok += 1
    else:
        print(f"FAIL {name}")
        for line in (r.stdout + r.stderr).strip().split("\n")[-4:]:
            print(f"   {line}")


ok = 0
total = 0

# ── 1. SkillDefinition ───────────────────────────────────────────────
T("SkillDefinition creation + trigger matching", """
from jiuzhang.skills_system import SkillDefinition

skill = SkillDefinition(
    name="deep-proof",
    description="Rigorous proof generation",
    triggers=["prove", "proof", "证明"],
    category="reasoning",
    tools=["sympy_compute", "verify_symbolic"],
    prompt="Do rigorous proofs.",
)
assert skill.name == "deep-proof"
assert skill.matches_trigger("prove that P != NP")
assert skill.matches_trigger("我需要一个证明")
assert not skill.matches_trigger("what is a prime number")

ctx = skill.to_system_context()
assert "[SKILL: deep-proof]" in ctx
assert "sympy_compute" in ctx
print("PASS")
""")

# ── 2. SkillLoader ───────────────────────────────────────────────────
T("SkillLoader discover + register", """
from jiuzhang.skills_system import SkillLoader, SkillDefinition

loader = SkillLoader()

# Register a skill manually
skill = SkillDefinition(name="test-skill", description="A test", triggers=["test"], category="test")
loader.register(skill)
assert loader.count() == 1

# Get by name
found = loader.get("test-skill")
assert found is not None
assert found.name == "test-skill"

# Get by trigger
matched = loader.get_by_trigger("this is a test of skills")
assert len(matched) == 1
assert matched[0].name == "test-skill"

# Get by category
cat_matched = loader.get_by_category("test")
assert len(cat_matched) == 1

# No match
no_match = loader.get_by_trigger("nothing here")
assert len(no_match) == 0

# List all
all_skills = loader.list_all()
assert len(all_skills) == 1
print("PASS")
""")

# ── 3. SkillManager (builtin skills) ─────────────────────────────────
T("SkillManager builtins + activation", """
from jiuzhang.skills_system import SkillManager

sm = SkillManager()

# Built-ins are auto-registered
skills = sm.list_available()
assert len(skills) >= 4, f"Expected >=4 built-in skills, got {len(skills)}"
names = [s["name"] for s in skills]
assert "deep-proof" in names
assert "counterexample-hunter" in names
assert "conjecture-generator" in names

# Activate by trigger
matched = sm.activate_by_trigger("please prove this theorem about prime numbers")
assert len(matched) >= 1

# Get active context
ctx = sm.get_active_context()
assert "[ACTIVE SKILLS]" in ctx
assert "deep-proof" in ctx

# Get active tools
tools = sm.get_active_tools()
assert len(tools) > 0
assert "sympy_compute" in tools

# Deactivate
sm.deactivate("deep-proof")
assert "deep-proof" not in sm._active_skills

# Activate another
sm.activate("counterexample-hunter")
ctx2 = sm.get_active_context()
assert "counterexample-hunter" in ctx2

# Reset
sm.reset()
assert len(sm._active_skills) == 0

print("PASS")
""")

# ── 4. MCPTool schema ────────────────────────────────────────────────
T("MCPTool + MCPServerConfig", """
from jiuzhang.mcp_client import MCPTool, MCPServerConfig

tool = MCPTool(
    name="wolfram_query",
    description="Query Wolfram Alpha",
    server_name="wolfram",
    parameters={"type": "object", "properties": {"query": {"type": "string"}}},
)
schema = tool.to_function_schema()
assert schema["type"] == "function"
assert schema["function"]["name"] == "wolfram_query"
assert "query" in str(schema["function"]["parameters"])

config = MCPServerConfig(
    name="test-server",
    command="echo",
    args=["hello"],
    description="A test server",
    timeout=10,
)
assert config.name == "test-server"
assert config.description == "A test server"
assert config.command == "echo"
assert config.args == ["hello"]
print("PASS")
""")

# ── 5. ToolDiscovery ─────────────────────────────────────────────────
T("ToolDiscovery all schemas", """
from jiuzhang.mcp_client import ToolDiscovery

td = ToolDiscovery()

# Get all tool schemas
schemas = td.get_all_tool_schemas()
assert len(schemas) >= 6, f"Expected >=6 built-in tools, got {len(schemas)}"

names = [s["function"]["name"] for s in schemas]
assert "sympy_compute" in names
assert "verify_equation" in names
assert "web_search" in names
assert "oeis_lookup" in names
assert "execute_code" in names

# Filter by category
verify_tools = td.get_tools_for_category("verify")
assert len(verify_tools) >= 1

compute_tools = td.get_tools_for_category("compute")
assert len(compute_tools) >= 1

# Register custom
def my_handler():
    return "ok"
td.register_custom_tool("my_tool", my_handler, {
    "type": "function",
    "function": {"name": "my_tool", "description": "Custom", "parameters": {}},
})
all_schemas = td.get_all_tool_schemas()
names2 = [s["function"]["name"] for s in all_schemas]
assert "my_tool" in names2

print("PASS")
""")

# ── 6. MCPClient construction ────────────────────────────────────────
T("MCPClient construction + tools", """
from jiuzhang.mcp_client import MCPClient, MCPServerConfig, BUILTIN_MCP_SERVERS

client = MCPClient()

# Add servers
client.add_builtin_servers()
servers = client.list_servers()
assert len(servers) >= 2, f"Expected >=2 servers, got {len(servers)}"

# Add manual server
client.add_server(MCPServerConfig(name="test", description="A test", command="echo", args=["hi"]))
servers2 = client.list_servers()
assert any(s["name"] == "test" for s in servers2)

# Tools initially empty (until connected)
tools = client.get_tools()
assert isinstance(tools, dict)

# Tool schemas
schemas = client.get_tool_schemas()
assert isinstance(schemas, list)

print("PASS")
""")

# ── Summary ──────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"Phase 4: {ok}/{total} passed")
if ok == total:
    print("ALL PHASE 4 TESTS PASSED")
else:
    print(f"SOME TESTS FAILED ({total - ok} failures)")
    sys.exit(1)
