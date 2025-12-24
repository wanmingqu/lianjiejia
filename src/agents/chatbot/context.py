from dataclasses import dataclass, field
from typing import Annotated, Callable

from src.agents.common import BaseContext, gen_tool_info
from src.agents.common.mcp import MCP_SERVERS

from .tools import get_tools


def get_dynamic_tools_info() -> Callable[[], list[dict]]:
    """动态获取工具信息，确保获取最新的知识库列表"""
    def _get_tools_info():
        try:
            tools = get_tools()  # 每次都重新获取最新的工具列表
            return gen_tool_info(tools)
        except Exception as e:
            from src.utils import logger
            logger.error(f"Failed to get dynamic tools info: {e}")
            return []
    
    return _get_tools_info


@dataclass(kw_only=True)
class Context(BaseContext):
    tools: Annotated[list[dict], {"__template_metadata__": {"kind": "tools"}}] = field(
        default_factory=list,
        metadata={
            "name": "工具",
            "options": get_dynamic_tools_info(),  # 改为动态获取
            "description": "工具列表",
        },
    )

    mcps: list[str] = field(
        default_factory=list,
        metadata={"name": "MCP服务器", "options": list(MCP_SERVERS.keys()), "description": "MCP服务器列表"},
    )

    # 流式输出控制
    streaming: bool = field(
        default=True,
        metadata={
            "name": "流式输出",
            "description": "是否启用流式输出，关闭后将等待完整响应后一次性返回",
        },
    )
