from dataclasses import dataclass, field
from typing import Annotated

from src.agents.common import BaseContext, gen_tool_info, get_buildin_tools
from src.agents.common.mcp import MCP_SERVERS
from src import knowledge_base

from .tools import get_tools, get_kb_manager


@dataclass(kw_only=True)
class Context(BaseContext):
    # 获取所有可用工具信息，包括知识库工具
    def _get_all_tools_info():
        """获取所有可用工具的信息，包括知识库工具和自定义工具"""
        try:
            # 获取知识库工具
            retrievers = knowledge_base.get_retrievers()
            kb_tools = []
            for db_id, info in retrievers.items():
                kb_tools.append({
                    "id": info['name'],
                    "name": info['name'],
                    "description": f"知识库: {info['description']}"
                })
            
            # 获取自定义工具
            custom_tools = gen_tool_info(get_tools())
            
            # 合并所有工具信息
            all_tools = kb_tools + custom_tools
            return all_tools
        except Exception:
            # 如果获取失败，返回自定义工具
            return gen_tool_info(get_tools())
    
    tools: Annotated[list[dict], {"__template_metadata__": {"kind": "tools"}}] = field(
        default_factory=list,
        metadata={
            "name": "工具",
            "options": _get_all_tools_info(),
            "description": "知识库查询相关工具列表",
        },
    )

    # 系统提示模板
    system_prompt_template: str = field(
        default="""你是专业的企业知识库查询助手，专门帮助员工查询公司内部规范、员工手册、政策制度等信息。

🔍 **核心查询能力**
- **政策制度查询**：公司章程、管理制度、业务规范
- **员工手册查询**：入职指南、行为准则、福利政策
- **流程规范查询**：工作流程、审批流程、操作指南
- **业务知识查询**：产品知识、服务标准、技术规范

📋 **查询策略建议**
1. **精确查询**：使用 `search_knowledge_base` 进行关键词精确搜索
2. **分类查询**：使用 `browse_knowledge_category` 按类别浏览
3. **最新更新**：使用 `get_latest_updates` 查询最新政策变更
4. **全文检索**：使用 `full_text_search` 进行深度内容搜索

⚡ **工作流程**
1. 分析用户查询需求 → 确定查询类型和关键词
2. 选择合适的查询工具 → 精确搜索或分类浏览
3. 整合查询结果 → 提供结构化、易读的回答
4. 补充相关信息 → 建议相关文档或后续查询

🎯 **重点关注**
- 政策制度的有效性和适用范围
- 员工手册的实用性和易理解性
- 流程规范的可操作性和时效性
- 业务知识的准确性和完整性

请根据用户的具体需求，灵活运用上述工具提供准确、及时的知识查询服务。对于复杂的查询需求，建议进行多轮搜索和交叉验证，确保信息的准确性和完整性。""",
        metadata={
            "name": "系统提示模板",
            "description": "AI助手的系统行为指导模板",
        },
    )

    mcps: list[str] = field(
        default_factory=list,
        metadata={"name": "MCP服务器", "options": list(MCP_SERVERS.keys()), "description": "MCP服务器列表"},
    )

    # 获取知识库选项
    def _get_knowledge_base_options():
        """获取系统中可用的知识库选项"""
        try:
            retrievers = knowledge_base.get_retrievers()
            kb_options = []
            for db_id, info in retrievers.items():
                kb_options.append(info['name'])
            return kb_options if kb_options else ["公司内部规范", "合同范本"]
        except Exception:
            return ["公司内部规范", "合同范本"]

    # 知识库选择配置，模仿ChatbotAgent的方式
    knowledge_bases: Annotated[list[str], {
        "__template_metadata__": {"kind": "select", "multiple": True},
        "name": "知识库选择",
        "description": "选择要查询的知识库",
        "placeholder": "请选择要使用的知识库...",
        "options": _get_knowledge_base_options()
    }] = field(default_factory=lambda: ["公司内部规范"], metadata={
        "name": "知识库选择",
        "description": "选择要查询的知识库",
        "placeholder": "请选择要使用的知识库...",
        "options": _get_knowledge_base_options()
    })

    # 知识库查询特定的配置项
    search_scope: str = field(
        default="全部",
        metadata={
            "name": "查询范围",
            "options": ["全部", "政策制度", "员工手册", "流程规范", "业务知识"],
            "description": "知识库查询的范围限制",
        },
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
        default=False,
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