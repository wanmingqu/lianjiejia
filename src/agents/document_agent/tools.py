"""文档撰写Agent工具集"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from langchain_core.tools import tool
from src.utils import logger

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.knowledge import KnowledgeBaseManager



# 单例知识库管理器
_kb_manager: Optional[KnowledgeBaseManager] = None

def get_kb_manager() -> KnowledgeBaseManager:
    """获取知识库管理器单例"""
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager(work_dir="./saves/knowledge_base_data")
    return _kb_manager

@tool
def generate_document(
    topic: str,
    document_type: str,
    key_points: Optional[List[str]] = None,
    target_audience: str = "专业人士"
) -> str:
    """
    生成文档的核心功能
    
    Args:
        topic: 文档主题
        document_type: 文档类型（技术文档、用户手册等）
        key_points: 关键要点列表
        target_audience: 目标受众
    
    Returns:
        生成的文档内容
    """
    try:
        kb_manager = get_kb_manager()
        
        # 构建搜索查询
        search_query = f"{topic} {document_type}"
        
        # 获取知识库内容
        kb_content = ""
        try:
            results = kb_manager.query(search_query, max_results=5)
            for result in results:
                if result.get('content'):
                    kb_content += result['content'] + "\n\n"
        except Exception as e:
            logger.warning(f"知识库查询失败，将基于通用知识生成: {e}")
        
        # 生成文档结构
        if document_type == "技术文档":
            document = generate_technical_document(topic, key_points, target_audience, kb_content)
        elif document_type == "用户手册":
            document = generate_user_manual(topic, key_points, target_audience, kb_content)
        elif document_type == "项目报告":
            document = generate_project_report(topic, key_points, target_audience, kb_content)
        elif document_type == "操作指南":
            document = generate_operation_guide(topic, key_points, target_audience, kb_content)
        else:
            document = generate_general_document(topic, document_type, key_points, target_audience, kb_content)
        
        return document
        
    except Exception as e:
        logger.error(f"文档生成失败: {e}")
        return f"文档生成失败: {str(e)}"

@tool
def search_knowledge_content(
    query: str,
    knowledge_bases: Optional[List[str]] = None,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    搜索知识库内容
    
    Args:
        query: 搜索查询词
        knowledge_bases: 指定知识库列表，None表示搜索所有
        max_results: 最大返回结果数
    
    Returns:
        搜索结果字典
    """
    try:
        kb_manager = get_kb_manager()
        
        results = []
        if knowledge_bases:
            # 搜索指定知识库
            for kb_name in knowledge_bases:
                try:
                    kb_results = kb_manager.query(query, max_results=max_results)
                    for result in kb_results:
                        result['source_kb'] = kb_name
                        results.append(result)
                except Exception as e:
                    logger.warning(f"搜索知识库 {kb_name} 失败: {e}")
        else:
            # 搜索所有知识库
            results = kb_manager.query(query, max_results=max_results)
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results[:max_results]
        }
        
    except Exception as e:
        logger.error(f"知识库搜索失败: {e}")
        return {
            "query": query,
            "total_results": 0,
            "results": [],
            "error": str(e)
        }

@tool
def get_template_structure(document_type: str) -> Dict[str, Any]:
    """
    获取文档模板结构
    
    Args:
        document_type: 文档类型
    
    Returns:
        文档模板结构
    """
    templates = {
        "技术文档": {
            "sections": [
                {"title": "概述", "required": True},
                {"title": "背景介绍", "required": True},
                {"title": "技术架构", "required": True},
                {"title": "实现细节", "required": True},
                {"title": "使用方法", "required": True},
                {"title": "注意事项", "required": False},
                {"title": "常见问题", "required": False},
                {"title": "参考资料", "required": True}
            ],
            "format": "markdown",
            "style": "专业"
        },
        "用户手册": {
            "sections": [
                {"title": "产品介绍", "required": True},
                {"title": "快速开始", "required": True},
                {"title": "功能说明", "required": True},
                {"title": "操作指南", "required": True},
                {"title": "故障排除", "required": False},
                {"title": "常见问题", "required": False},
                {"title": "联系方式", "required": False}
            ],
            "format": "markdown",
            "style": "简洁明了"
        },
        "项目报告": {
            "sections": [
                {"title": "执行摘要", "required": True},
                {"title": "项目背景", "required": True},
                {"title": "项目目标", "required": True},
                {"title": "实施过程", "required": True},
                {"title": "成果展示", "required": True},
                {"title": "数据分析", "required": True},
                {"title": "问题与挑战", "required": False},
                {"title": "经验总结", "required": True},
                {"title": "后续建议", "required": True}
            ],
            "format": "markdown",
            "style": "正式专业"
        },
        "操作指南": {
            "sections": [
                {"title": "准备工作", "required": True},
                {"title": "操作步骤", "required": True},
                {"title": "注意事项", "required": True},
                {"title": "常见错误", "required": False},
                {"title": "维护建议", "required": False}
            ],
            "format": "markdown",
            "style": "详细步骤"
        }
    }
    
    return templates.get(document_type, {
        "sections": [
            {"title": "引言", "required": True},
            {"title": "正文", "required": True},
            {"title": "结论", "required": True}
        ],
        "format": "markdown",
        "style": "标准"
    })

@tool
def optimize_content(content: str, optimization_type: str = "readability") -> str:
    """
    优化文档内容
    
    Args:
        content: 待优化内容
        optimization_type: 优化类型（readability, clarity, completeness）
    
    Returns:
        优化后的内容
    """
    try:
        # 基础优化处理
        if optimization_type == "readability":
            # 提升可读性
            content = improve_readability(content)
        elif optimization_type == "clarity":
            # 提升清晰度
            content = improve_clarity(content)
        elif optimization_type == "completeness":
            # 提升完整性
            content = improve_completeness(content)
        
        return content
        
    except Exception as e:
        logger.error(f"内容优化失败: {e}")
        return content

@tool
def format_document(content: str, output_format: str = "markdown") -> str:
    """
    格式化文档输出
    
    Args:
        content: 文档内容
        output_format: 输出格式（markdown, html, text）
    
    Returns:
        格式化后的文档
    """
    try:
        if output_format.lower() == "html":
            return convert_to_html(content)
        elif output_format.lower() == "text":
            return convert_to_text(content)
        else:
            return content  # 默认返回markdown格式
            
    except Exception as e:
        logger.error(f"文档格式化失败: {e}")
        return content

@tool
def validate_content(content: str, validation_type: str = "basic") -> Dict[str, Any]:
    """
    验证文档内容
    
    Args:
        content: 文档内容
        validation_type: 验证类型（basic, comprehensive, technical）
    
    Returns:
        验证结果
    """
    validation_result = {
        "is_valid": True,
        "issues": [],
        "suggestions": [],
        "stats": {}
    }
    
    try:
        # 基础验证
        if not content.strip():
            validation_result["is_valid"] = False
            validation_result["issues"].append("文档内容为空")
        
        # 统计信息
        validation_result["stats"] = {
            "character_count": len(content),
            "word_count": len(content.split()),
            "line_count": content.count('\n') + 1
        }
        
        # 结构验证
        if '##' not in content and len(content) > 200:
            validation_result["suggestions"].append("建议添加标题和子标题以改善结构")
        
        # 技术验证
        if validation_type in ["comprehensive", "technical"]:
            # 检查是否有引用
            if '[' not in content and '参考' not in content:
                validation_result["suggestions"].append("建议添加参考文献")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"内容验证失败: {e}")
        validation_result["is_valid"] = False
        validation_result["issues"].append(f"验证过程出错: {str(e)}")
        return validation_result

# 辅助函数
def generate_technical_document(topic: str, key_points: List[str], audience: str, kb_content: str) -> str:
    """生成技术文档"""
    doc = f"# {topic} 技术文档\n\n"
    doc += "## 概述\n\n"
    doc += f"本文档详细介绍{topic}的相关技术内容。\n\n"
    
    if kb_content:
        doc += "## 背景知识\n\n"
        doc += f"{kb_content[:500]}...\n\n"
    
    doc += "## 技术实现\n\n"
    if key_points:
        for i, point in enumerate(key_points, 1):
            doc += f"{i}. {point}\n"
    else:
        doc += "此处应包含具体的技术实现细节。\n"
    
    doc += "\n## 参考资料\n\n"
    doc += "* 相关技术文档\n"
    doc += "* 官方API文档\n"
    
    return doc

def generate_user_manual(topic: str, key_points: List[str], audience: str, kb_content: str) -> str:
    """生成用户手册"""
    doc = f"# {topic} 用户手册\n\n"
    doc += "## 产品介绍\n\n"
    doc += f"欢迎使用{topic}！本手册将帮助您快速上手。\n\n"
    
    doc += "## 快速开始\n\n"
    doc += "1. 环境准备\n"
    doc += "2. 安装配置\n"
    doc += "3. 基本使用\n\n"
    
    if key_points:
        doc += "## 主要功能\n\n"
        for point in key_points:
            doc += f"- {point}\n"
        doc += "\n"
    
    doc += "## 常见问题\n\n"
    doc += "如有问题，请参考FAQ或联系技术支持。\n"
    
    return doc

def generate_project_report(topic: str, key_points: List[str], audience: str, kb_content: str) -> str:
    """生成项目报告"""
    doc = f"# {topic} 项目报告\n\n"
    doc += "## 执行摘要\n\n"
    doc += f"本项目围绕{topic}展开，取得了预期成果。\n\n"
    
    doc += "## 项目背景\n\n"
    doc += f"{topic}项目旨在解决相关问题。\n\n"
    
    if key_points:
        doc += "## 主要成果\n\n"
        for i, point in enumerate(key_points, 1):
            doc += f"{i}. {point}\n"
        doc += "\n"
    
    doc += "## 数据分析\n\n"
    doc += "项目数据分析显示效果良好。\n\n"
    
    doc += "## 经验总结\n\n"
    doc += "通过本项目，我们积累了宝贵经验。\n"
    
    return doc

def generate_operation_guide(topic: str, key_points: List[str], audience: str, kb_content: str) -> str:
    """生成操作指南"""
    doc = f"# {topic} 操作指南\n\n"
    doc += "## 准备工作\n\n"
    doc += "在开始操作前，请确保以下条件已满足：\n\n"
    
    doc += "## 操作步骤\n\n"
    if key_points:
        for i, step in enumerate(key_points, 1):
            doc += f"{i}. {step}\n"
    else:
        doc += "1. 第一步操作\n"
        doc += "2. 第二步操作\n"
        doc += "3. 第三步操作\n"
    
    doc += "\n## 注意事项\n\n"
    doc += "- 请严格按照步骤操作\n"
    doc += "- 注意安全防护措施\n"
    doc += "- 如遇问题请及时求助\n"
    
    return doc

def generate_general_document(topic: str, doc_type: str, key_points: List[str], audience: str, kb_content: str) -> str:
    """生成通用文档"""
    doc = f"# {topic}\n\n"
    doc += f"## 关于{doc_type}\n\n"
    doc += f"这是关于{topic}的{doc_type}。\n\n"
    
    if key_points:
        doc += "## 主要内容\n\n"
        for point in key_points:
            doc += f"- {point}\n"
        doc += "\n"
    
    doc += "## 总结\n\n"
    doc += f"以上是关于{topic}的{doc_type}内容。\n"
    
    return doc

def improve_readability(content: str) -> str:
    """提升可读性"""
    # 简单的可读性优化
    lines = content.split('\n')
    improved_lines = []
    
    for line in lines:
        # 确保段落间有空行
        if line.strip() and len(line) > 100:
            if not line.endswith(('。', '！', '？')):
                line += '。'
        improved_lines.append(line)
    
    return '\n'.join(improved_lines)

def improve_clarity(content: str) -> str:
    """提升清晰度"""
    # 简单的清晰度优化
    content = re.sub(r'就是', '是', content)
    content = re.sub(r'的话', '', content)
    return content

def improve_completeness(content: str) -> str:
    """提升完整性"""
    if not content.endswith(('。', '！', '？')):
        content += '。'
    return content

def convert_to_html(content: str) -> str:
    """转换为HTML格式"""
    html = "<html><head><title>Document</title></head><body>"
    lines = content.split('\n')
    
    for line in lines:
        if line.startswith('# '):
            html += f"<h1>{line[2:]}</h1>"
        elif line.startswith('## '):
            html += f"<h2>{line[3:]}</h2>"
        elif line.startswith('### '):
            html += f"<h3>{line[4:]}</h3>"
        elif line.strip():
            html += f"<p>{line}</p>"
        else:
            html += "<br>"
    
    html += "</body></html>"
    return html

def convert_to_text(content: str) -> str:
    """转换为纯文本格式"""
    text = content
    text = re.sub(r'^#+\s', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    return text


@tool
def play_completion_notification(
    task_type: str = "文档生成",
    success: bool = True,
    voice_type: str = "女声"
) -> str:
    """
    在任务完成后播放语音提示，提醒用户及时查看结果
    
    Args:
        task_type: 任务类型，如"文档生成"、"内容优化"等
        success: 任务是否成功完成
        voice_type: 语音类型，如"女声"、"男声"
    
    Returns:
        语音提示执行状态信息
    """
    try:
        import platform
        import subprocess
        
        if success:
            message = f"您的{task_type}任务已成功完成，请及时查看结果！"
        else:
            message = f"您的{task_type}任务遇到问题，请查看详细信息。"
        
        system = platform.system()
        
        if system == "Windows":
            # Windows 使用系统语音
            import win32com.client as wincl
            speaker = wincl.Dispatch("SAPI.SpVoice")
            if voice_type == "女声":
                speaker.Voice = speaker.GetVoices('Name=Microsoft Zira Desktop').Item(0)
            else:
                speaker.Voice = speaker.GetVoices('Name=Microsoft David Desktop').Item(0)
            speaker.Speak(message)
            
        elif system == "Darwin":  # macOS
            # macOS 使用 say 命令
            voice = "Ting-Ting" if voice_type == "女声" else "Alex"
            subprocess.run(['say', '-v', voice, message], check=False)
            
        elif system == "Linux":
            # Linux 尝试使用 espeak 或 festival
            try:
                subprocess.run(['espeak', '-s', '150', '-v', 'zh', message], check=False)
            except FileNotFoundError:
                try:
                    subprocess.run(['festival', '--batch', f'(SayText "{message}")'], check=False)
                except FileNotFoundError:
                    logger.warning("未找到语音合成工具，请安装 espeak 或 festival")
                    return "语音提示功能不可用，请安装 espeak 或 festival"
        
        logger.info(f"已播放语音提示: {message}")
        return f"✅ 语音提示已播放: {message}"
        
    except Exception as e:
        logger.error(f"播放语音提示失败: {e}")
        return f"❌ 语音提示播放失败: {str(e)}"


@tool
def analyze_document_completion(
    document_content: str,
    task_requirements: str
) -> Dict[str, Any]:
    """
    分析文档完成情况并触发语音提示
    
    Args:
        document_content: 生成的文档内容
        task_requirements: 任务需求描述
    
    Returns:
        包含完成度分析和语音提示状态的结果
    """
    try:
        # 简单的完成度分析
        content_length = len(document_content)
        requirements_met = True  # 这里可以添加更复杂的逻辑
        
        # 判断是否成功完成
        success = content_length > 100 and requirements_met
        
        # 触发语音提示
        notification_result = play_completion_notification(
            task_type="文档生成",
            success=success
        )
        
        return {
            "content_length": content_length,
            "requirements_met": requirements_met,
            "success": success,
            "notification": notification_result
        }
        
    except Exception as e:
        logger.error(f"分析文档完成情况失败: {e}")
        return {
            "error": str(e),
            "success": False
        }