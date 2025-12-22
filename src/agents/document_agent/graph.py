"""文档撰写Agent图实现"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from src.agents.common import BaseAgent
from src.agents.document_agent.context import Context
from src.utils import logger



class DocumentAgent(BaseAgent):
    """文档撰写Agent"""
    name = "文档撰写助手"
    description = "专业的文档撰写Agent，具备知识库选择功能，能够基于知识库内容生成高质量文档"
    capabilities = ["document_generation", "knowledge_base_integration", "content_optimization"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.graph = None
        self.checkpointer = None
        self._agent_runnable = None
        self._tools: List[BaseTool] = []
        self.context_schema = Context
        
    def _build_agent_graph(self):
        """构建Agent图"""
        from langchain.agents import create_agent
        from langchain_core.prompts import ChatPromptTemplate
        
        # 获取工具
        tools = self._get_tools()
        self._tools = tools
        
        # 创建系统提示
        system_prompt = self._get_system_prompt()
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("placeholder", "{messages}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # 创建模型
        model = self._get_model()
        
        # 创建Agent
        agent = create_agent(
            model,
            tools,
            prompt
        )
        
        return agent
    
    def _get_tools(self) -> List[BaseTool]:
        """获取工具列表"""
        tools = []
        
        try:
            from .tools import (
                generate_document,
                search_knowledge_content,
                get_template_structure,
                optimize_content,
                format_document,
                validate_content,
                play_completion_notification,
                analyze_document_completion
            )
            
            document_tools = [
                generate_document,
                search_knowledge_content,
                get_template_structure,
                optimize_content,
                format_document,
                validate_content,
                play_completion_notification,
                analyze_document_completion
            ]
            
            tools.extend(document_tools)
            logger.info(f"加载文档撰写工具: {len(document_tools)}个")
            
        except Exception as e:
            logger.error(f"加载文档撰写工具失败: {e}")
        
        return tools
    
    def _get_system_prompt(self, context: Context = None) -> str:
        """获取系统提示词"""
        if context is None:
            # 使用默认Context
            context = Context()
        
        # 替换模板变量
        prompt = context.system_prompt_template
        
        # 添加配置信息
        config_info = f"""
## 当前配置
- 文档类型: {context.document_type}
- 输出格式: {context.output_format}
- 写作风格: {context.writing_style}
- 知识库依赖度: {context.knowledge_dependency}
- 包含参考文献: {'是' if context.include_references else '否'}
- 自动优化: {'是' if context.auto_optimize else '否'}
- 启用知识库: {', '.join(context.knowledge_bases) if context.knowledge_bases else '无'}
"""
        
        prompt += config_info
        
        return prompt
    
    def _get_model(self):
        """获取模型"""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=4000
        )
    
    async def get_graph(self, **kwargs) -> CompiledStateGraph:
        """获取编译后的图实例"""
        from langchain.agents import create_agent
        from src.agents.common import load_chat_model
        
        if self.graph:
            return self.graph

        # 使用 create_agent 创建智能体，使用简化的实现
        graph = create_agent(
            model=load_chat_model("siliconflow/Qwen/Qwen3-235B-A22B-Instruct-2507"),
            tools=self._get_tools(),
            checkpointer=await self._get_checkpointer(),
        )

        self.graph = graph
        return graph
    
    async def stream_messages(self, messages: list[str], input_context=None, **kwargs):
        """重写流式消息处理方法，支持语音提示"""
        # 获取上下文配置
        context = self.context_schema.from_file(module_name=self.module_name, input_context=input_context)
        
        # 调用父类的流式处理方法
        async for msg, metadata in super().stream_messages(messages, input_context=input_context, **kwargs):
            yield msg, metadata
        
        # 如果启用了语音提示功能，在流式处理结束后播放提示
        if getattr(context, 'enable_voice_notification', False):
            try:
                # 使用语音工具播放提示
                from .tools import play_completion_notification
                voice_type = getattr(context, 'voice_type', '女声')
                notification_result = play_completion_notification(
                    task_type="文档生成",
                    success=True,
                    voice_type=voice_type
                )
                logger.info(f"语音提示结果: {notification_result}")
            except Exception as voice_error:
                logger.warning(f"语音提示功能执行失败: {voice_error}")
    

    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        if not self._tools:
            self._get_tools()
        
        tools_info = []
        for tool in self._tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "type": "document_tool"
            })
        
        return tools_info
    
    def get_context_info(self, context: Optional[Context] = None) -> Dict[str, Any]:
        """获取上下文信息"""
        if context is None:
            context = Context()
            
        return {
            "document_type": context.document_type,
            "output_format": context.output_format,
            "writing_style": context.writing_style,
            "knowledge_dependency": context.knowledge_dependency,
            "knowledge_bases": context.knowledge_bases,
            "include_references": context.include_references,
            "auto_optimize": context.auto_optimize,
            "enable_version_control": context.enable_version_control
        }