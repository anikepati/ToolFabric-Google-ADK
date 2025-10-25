from tools.mcp_based_tool import MCPBasedTool
from tools.internal_function_tool import InternalFunctionTool

def create_tool(tool_cfg):
    if "command" in tool_cfg:
        return MCPBasedTool(tool_cfg["name"], tool_cfg)
    elif "module" in tool_cfg and "function" in tool_cfg:
        return InternalFunctionTool(tool_cfg["name"], tool_cfg)
    else:
        raise ValueError(f"Unknown tool type for {tool_cfg['name']}")
