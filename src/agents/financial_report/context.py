"""财报分析Agent上下文配置"""

from dataclasses import dataclass, field
from typing import Annotated, Any, Callable, List

from src.agents.common import BaseContext, gen_tool_info, get_mcp_tools
from src.agents.common.mcp import MCP_SERVERS
from src.utils import logger

from .tools import get_tools


def get_dynamic_tools_info() -> Callable[[], list[dict]]:
    """动态获取工具信息，确保获取最新的工具列表"""
    def _get_tools_info():
        try:
            tools = get_tools()  # 每次都重新获取最新的工具列表
            return gen_tool_info(tools)
        except Exception as e:
            from src.utils import logger
            logger.error(f"Failed to get dynamic tools info: {e}")
            return []
    
    return _get_tools_info


def _get_chart_types():
    """获取支持的图表类型选项"""
    return [
        {"value": "line", "label": "折线图"},
        {"value": "bar", "label": "柱状图"},
        {"value": "pie", "label": "饼图"},
        {"value": "scatter", "label": "散点图"},
        {"value": "area", "label": "面积图"},
        {"value": "radar", "label": "雷达图"},
        {"value": "heatmap", "label": "热力图"},
    ]


def _get_financial_metrics():
    """获取财务指标选项"""
    return [
        {"value": "revenue", "label": "营业收入"},
        {"value": "net_profit", "label": "净利润"},
        {"value": "total_assets", "label": "总资产"},
        {"value": "total_liabilities", "label": "总负债"},
        {"value": "current_assets", "label": "流动资产"},
        {"value": "current_liabilities", "label": "流动负债"},
        {"value": "cash_flow", "label": "现金流"},
        {"value": "roe", "label": "净资产收益率"},
        {"value": "roa", "label": "总资产收益率"},
        {"value": "debt_ratio", "label": "资产负债率"},
        {"value": "current_ratio", "label": "流动比率"},
        {"value": "quick_ratio", "label": "速动比率"},
    ]


@dataclass(kw_only=True)
class Context(BaseContext):
    """财报分析Agent上下文配置"""
    
    # 动态工具配置（必需字段）
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
    
    # 图表配置
    default_chart_type: Annotated[str, {
        "__template_metadata__": {"kind": "select"},
        "name": "默认图表类型",
        "description": "选择默认的图表类型",
        "options": _get_chart_types()
    }] = field(default="bar")
    
    # 数据提取配置
    extract_tables: Annotated[bool, {
        "__template_metadata__": {"kind": "checkbox"},
        "name": "提取表格数据",
        "description": "是否从PDF中提取表格数据"
    }] = field(default=True)
    
    extract_text: Annotated[bool, {
        "__template_metadata__": {"kind": "checkbox"},
        "name": "提取文本数据",
        "description": "是否从PDF中提取文本数据"
    }] = field(default=True)
    
    # 财务指标配置
    primary_metrics: Annotated[List[str], {
        "__template_metadata__": {"kind": "multi_select"},
        "name": "主要财务指标",
        "description": "选择重点分析的财务指标",
        "options": _get_financial_metrics()
    }] = field(default_factory=lambda: ["revenue", "net_profit", "total_assets"])
    
    # 分析维度配置
    analysis_dimensions: Annotated[List[str], {
        "__template_metadata__": {"kind": "multi_select"},
        "name": "分析维度",
        "description": "选择财报分析的维度",
        "options": [
            {"value": "profitability", "label": "盈利能力"},
            {"value": "solvency", "label": "偿债能力"},
            {"value": "operational", "label": "运营能力"},
            {"value": "growth", "label": "成长能力"},
            {"value": "cash_flow", "label": "现金流分析"},
        ]
    }] = field(default_factory=lambda: ["profitability", "solvency"])
    
    # 图表样式配置
    chart_theme: Annotated[str, {
        "__template_metadata__": {"kind": "radio"},
        "name": "图表主题",
        "description": "选择图表的视觉主题",
        "options": ["light", "dark", "colorful", "professional"]
    }] = field(default="professional")
    
    chart_size: Annotated[str, {
        "__template_metadata__": {"kind": "radio"},
        "name": "图表尺寸",
        "description": "选择生成的图表尺寸",
        "options": ["small", "medium", "large", "extra_large"]
    }] = field(default="medium")
    
    # 数值配置
    years_comparison: Annotated[int, {
        "__template_metadata__": {"kind": "slider"},
        "name": "对比年数",
        "description": "设置对比分析的年数（1-10年）",
        "min": 1,
        "max": 10,
        "step": 1
    }] = field(default=3)
    
    decimal_places: Annotated[int, {
        "__template_metadata__": {"kind": "slider"},
        "name": "小数位数",
        "description": "财务数据显示的小数位数",
        "min": 0,
        "max": 4,
        "step": 1
    }] = field(default=2)
    
    # 高级配置
    enable_multi_company: Annotated[bool, {
        "__template_metadata__": {"kind": "checkbox"},
        "name": "多公司对比",
        "description": "启用多公司财报对比分析功能"
    }] = field(default=False)
    
    calculate_ratios: Annotated[bool, {
        "__template_metadata__": {"kind": "checkbox"},
        "name": "计算财务比率",
        "description": "自动计算各类财务比率指标"
    }] = field(default=True)
    
    generate_report: Annotated[bool, {
        "__template_metadata__": {"kind": "checkbox"},
        "name": "生成分析报告",
        "description": "生成完整的财务分析报告"
    }] = field(default=True)
    
    # 流式输出控制
    streaming: bool = field(
        default=True,
        metadata={
            "name": "流式输出",
            "description": "是否启用流式输出，关闭后将等待完整响应后一次性返回",
        },
    )
    
    # 系统提示词
    system_prompt_template: str = field(
        default="""你是一位专业的财务分析师，具备深厚的财务知识和数据分析能力。

## 核心职责
- 解析上市公司财务报表PDF文件，提取关键财务数据
- 进行多维度财务分析，包括盈利能力、偿债能力、运营能力等
- 生成专业的财务分析图表和可视化报告
- 提供基于数据的财务建议和风险提示

## 专业能力
- 熟练解读三大财务报表：资产负债表、利润表、现金流量表
- 精通各类财务比率和指标的计算与分析
- 具备财务数据可视化和图表生成能力
- 了解会计准则和财务报告规范

## 工作流程
1. **文件解析**: 上传并解析财务报表PDF文件
2. **数据提取**: 提取关键财务数据和指标
3. **财务分析**: 计算财务比率，分析财务状况
4. **图表生成**: 生成多维度财务分析图表
5. **报告撰写**: 撰写专业的财务分析报告

## 输出要求
- 提供准确、清晰的财务数据分析
- 生成专业的可视化图表
- 给出有价值的财务建议和风险提示
- 确保分析结论基于可靠数据

请根据用户的需求，使用专业工具提供高质量的财务分析服务。""",
        metadata={
            "name": "系统提示词模板",
            "description": "财报分析Agent的系统提示词模板"
        }
    )