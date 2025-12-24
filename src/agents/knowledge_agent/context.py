from dataclasses import dataclass, field
from typing import Annotated

from src.agents.common import BaseContext, gen_tool_info, get_buildin_tools
from src.agents.common.mcp import MCP_SERVERS


def get_dynamic_knowledge_tools_info():
    """动态获取知识库工具信息"""
    try:
        return gen_tool_info(get_buildin_tools())
    except Exception as e:
        from src.utils import logger
        logger.error(f"Failed to get knowledge tools info: {e}")
        return []


@dataclass(kw_only=True)
class Context(BaseContext):
    tools: Annotated[list[dict], {"__template_metadata__": {"kind": "tools"}}] = field(
        default_factory=lambda: gen_tool_info(get_buildin_tools()),
        metadata={
            "name": "工具",
            "options": get_dynamic_knowledge_tools_info(),
            "description": "知识库查询相关工具列表",
        },
    )

    mcps: list[str] = field(
        default_factory=list,
        metadata={"name": "MCP服务器", "options": list(MCP_SERVERS.keys()), "description": "MCP服务器列表"},
    )

    result_format: str = field(
        default="详细",
        metadata={
            "name": "结果格式",
            "options": ["简洁", "详细", "汇总"],
            "description": "查询结果的展示格式",
        },
    )

    # 流式输出控制
    streaming: bool = field(
        default=True,
        metadata={
            "name": "流式输出",
            "description": "是否启用流式输出，关闭后将等待完整响应后一次性返回",
        },
    )

    # 思考过程控制
    show_thinking: bool = field(
        default=False,
        metadata={
            "name": "显示思考过程",
            "description": "是否显示大模型的思考过程和推理步骤",
        },
    )