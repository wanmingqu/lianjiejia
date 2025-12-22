"""文档撰写Agent上下文配置"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, TypeVar

from src.agents.common import BaseContext
from src.utils import logger

# 在获取知识库选项时再导入，避免循环导入

# 使用logger模块


T = TypeVar('T')

def _get_knowledge_base_options():
    """动态获取知识库选项"""
    try:
        from src import knowledge_base
        retrievers = knowledge_base.get_retrievers()
        return [info['name'] for db_id, info in retrievers.items()]
    except Exception as e:
        logger.error(f"获取知识库选项失败: {e}")
        return ["默认知识库"]

def _get_document_templates():
    """获取文档模板选项"""
    return [
        "技术文档",
        "用户手册", 
        "项目报告",
        "操作指南",
        "产品说明",
        "会议纪要",
        "调研报告",
        "培训材料"
    ]

def _get_available_tools() -> list[dict[str, Any]]:
    """获取文档撰写工具列表"""
    tools = []
    
    try:
        from .tools import (
            generate_document,
            search_knowledge_content,
            get_template_structure,
            optimize_content,
            format_document,
            validate_content
        )
        
        document_tools = [
            generate_document,
            search_knowledge_content,
            get_template_structure,
            optimize_content,
            format_document,
            validate_content
        ]
        
        for tool in document_tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "type": "document"
            })
            
    except Exception as e:
        logger.error(f"获取文档撰写工具失败: {e}")
    
    # 获取知识库工具
    try:
        from src import knowledge_base
        retrievers = knowledge_base.get_retrievers()
        for db_id, info in retrievers.items():
            tools.append({
                "name": f"kb_search_{db_id}",
                "description": f"搜索 {info['name']} 知识库",
                "type": "knowledge_base"
            })
    except Exception as e:
        logger.error(f"获取知识库工具失败: {e}")
    
    return tools

@dataclass
class Context(BaseContext):
    """文档撰写Agent上下文"""
    
    # 知识库选择
    knowledge_bases: Annotated[list[str], {
        "__template_metadata__": {"kind": "select", "multiple": True},
        "name": "知识库选择",
        "description": "选择用于文档撰写的知识库，将基于选定知识库的内容生成文档",
        "options": _get_knowledge_base_options()
    }] = field(default_factory=list)
    
    # 文档类型
    document_type: Annotated[str, {
        "__template_metadata__": {"kind": "select", "multiple": False},
        "name": "文档类型",
        "description": "选择要生成的文档类型",
        "options": _get_document_templates()
    }] = field(default="技术文档")
    
    # 输出格式
    output_format: Annotated[str, {
        "__template_metadata__": {"kind": "radio", "multiple": False},
        "name": "输出格式",
        "description": "选择文档输出格式",
        "options": ["Markdown", "HTML", "纯文本"]
    }] = field(default="Markdown")
    
    # 文档风格
    writing_style: Annotated[str, {
        "__template_metadata__": {"kind": "radio", "multiple": False},
        "name": "写作风格",
        "description": "选择文档写作风格",
        "options": ["正式专业", "简洁明了", "通俗易懂", "详细深入"]
    }] = field(default="正式专业")
    
    # 知识库依赖度
    knowledge_dependency: Annotated[str, {
        "__template_metadata__": {"kind": "slider", "multiple": False},
        "name": "知识库依赖度",
        "description": "控制生成内容对知识库的依赖程度（0%为完全原创，100%为完全基于知识库）",
        "min": 0,
        "max": 100,
        "step": 10,
        "unit": "%"
    }] = field(default="70%")
    
    # 工具配置
    tools: list[dict] = field(
        default_factory=_get_available_tools,
        metadata={
            "name": "可用工具",
            "description": "文档撰写可用的工具列表"
        }
    )
    
    # 运行时选项
    include_references: Annotated[bool, {
        "__template_metadata__": {"kind": "checkbox"},
        "name": "包含参考文献",
        "description": "是否在文档中包含知识库来源引用"
    }] = field(default=True)
    
    auto_optimize: Annotated[bool, {
        "__template_metadata__": {"kind": "checkbox"},
        "name": "自动优化",
        "description": "是否自动优化生成的内容质量和可读性"
    }] = field(default=True)
    
    # 高级配置
    enable_version_control: Annotated[bool, {
        "__template_metadata__": {"kind": "checkbox"},
        "name": "版本控制",
        "description": "是否启用文档版本控制功能"
    }] = field(default=False)
    
    # 语音通知配置
    enable_voice_notification: Annotated[bool, {
        "__template_metadata__": {"kind": "checkbox"},
        "name": "语音提示",
        "description": "任务完成后是否播放语音提示提醒用户查看"
    }] = field(default=True)
    
    voice_type: Annotated[str, {
        "__template_metadata__": {"kind": "radio", "multiple": False},
        "name": "语音类型",
        "description": "选择语音提示的声音类型",
        "options": ["女声", "男声"]
    }] = field(default="女声")
    
    # 系统提示模板
    system_prompt_template: str = field(
        default="""你是一个专业的文档撰写助手，具备强大的知识库整合能力。

## 核心能力
- 基于选定的知识库内容生成专业文档
- 支持多种文档类型和格式输出
- 智能整合知识库信息，确保内容准确权威
- 根据指定风格优化文档可读性

## 工作流程
1. **理解需求**: 分析用户文档需求和类型
2. **知识检索**: 基于选定知识库搜索相关内容
3. **内容整合**: 将知识库内容与用户需求结合
4. **结构设计**: 按照标准模板组织文档结构
5. **内容生成**: 撰写专业、准确的文档内容
6. **质量优化**: 根据配置优化文档质量

## 文档类型指导
- **技术文档**: 注重准确性、结构化、专业性
- **用户手册**: 强调易用性、步骤清晰、实例丰富
- **项目报告**: 突出数据支撑、逻辑严谨、结论明确
- **操作指南**: 侧重步骤详细、操作可行、注意事项

## 知识库使用原则
- 优先使用知识库中的权威内容
- 注明信息来源，确保可追溯性
- 综合多个知识源，提高内容完整性
- 当知识库内容不足时，合理补充专业内容

## 输出要求
- 保持专业性和准确性
- 结构清晰，逻辑性强
- 符合指定的格式和风格要求
- 包含必要的引用和参考文献

请基于用户的配置和需求，生成高质量的文档内容。""",
        metadata={
            "name": "系统提示词模板",
            "description": "Agent的系统提示词模板"
        }
    )