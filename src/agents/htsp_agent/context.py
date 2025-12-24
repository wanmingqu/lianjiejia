from dataclasses import dataclass, field
from typing import Annotated

from src.agents.common import BaseContext, gen_tool_info
from src.agents.common.mcp import MCP_SERVERS

from .tools import get_tools


@dataclass(kw_only=True)
class Context(BaseContext):
    tools: Annotated[list[dict], {"__template_metadata__": {"kind": "tools"}}] = field(
        default_factory=list,
        metadata={
            "name": "工具",
            "options": gen_tool_info(get_tools()),
            "description": "合同审批相关工具列表",
        },
    )

    # 系统提示模板
    system_prompt_template: str = field(
        default="""你是专业的合同审批助手，具备以下核心能力：

🔍 **文件处理能力**
- 支持PDF、Word(.docx)、文本(.txt)文件的上传和解析
- 可提取文件中的合同文本内容进行分析
- 支持多种文档格式的智能识别和转换

📋 **合同审核功能**
- **结构分析**：识别合同关键条款、检查必备要素、发现风险指标
- **合规检查**：验证法律、财务、商业等多维度合规性
- **风险评估**：评估合同风险等级，识别潜在问题
- **综合报告**：生成完整的审核报告和改进建议

⚡ **工作流程建议**
1. 用户上传合同文件 → 使用 `upload_contract_file` 验证文件
2. 提取文本内容 → 使用 `extract_contract_text` 获取合同文本
3. 执行审核分析 → 使用 `comprehensive_contract_review` 进行全面审核
4. 或分步审核 → 使用 `analyze_contract_structure` + `validate_contract_compliance`

🎯 **重点关注**
- 当事人信息完整性
- 合同条款明确性
- 风险责任分配合理性
- 法律合规性检查
- 财务条款安全性

请根据用户需求，灵活使用上述工具提供专业、准确的合同审批服务。对于复杂的合同，建议进行多维度综合审核，并提供详细的风险提示和改进建议。""",
        metadata={
            "name": "系统提示模板",
            "description": "AI助手的系统行为指导模板",
        },
    )

    mcps: list[str] = field(
        default_factory=list,
        metadata={"name": "MCP服务器", "options": list(MCP_SERVERS.keys()), "description": "MCP服务器列表"},
    )

    # 合同审批特定的配置项
    risk_level: str = field(
        default="中等",
        metadata={
            "name": "风险等级",
            "options": ["低", "中等", "高"],
            "description": "合同风险评估的严格程度",
        },
    )

    check_types: list[str] = field(
        default_factory=lambda: ["法律", "财务", "商业"],
        metadata={
            "name": "检查类型",
            "options": ["法律", "财务", "商业", "技术", "合规"],
            "description": "合同审核的重点领域",
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