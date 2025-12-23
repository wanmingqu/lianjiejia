from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware

from src.agents.common import BaseAgent, load_chat_model
from src.agents.common.mcp import MCP_SERVERS
from src.agents.common.middlewares import (
    DynamicToolMiddleware,
    context_aware_prompt,
    context_based_model,
    inject_attachment_context,
)
from src.agents.common.subagents import calc_agent_tool

from .context import Context
from src.agents.common import get_buildin_tools


class KnowledgeAgent(BaseAgent):
    name = "知识库查询助手"
    description = "专门用于查询公司内部知识库的智能助手，支持政策制度、员工手册、流程规范、业务知识等信息查询。"
    capabilities = ["search", "document_retrieval"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.graph = None
        self.checkpointer = None
        self.context_schema = Context

    def get_tools(self):
        """返回知识库查询相关工具 - 使用标准工具体系"""
        base_tools = get_buildin_tools()  # 使用标准的知识库工具体系
        base_tools.append(calc_agent_tool)
        return base_tools

    async def get_graph(self, **kwargs):
        """构建图"""
        if self.graph:
            return self.graph

        # 创建动态工具中间件实例，并传入所有可用的 MCP 服务器列表
        dynamic_tool_middleware = DynamicToolMiddleware(
            base_tools=self.get_tools(), mcp_servers=list(MCP_SERVERS.keys())
        )

        # 预加载所有 MCP 工具并注册到 middleware.tools
        await dynamic_tool_middleware.initialize_mcp_tools()

        # 使用 create_agent 创建智能体，并传入 middleware
        graph = create_agent(
            model=load_chat_model("siliconflow/Qwen/Qwen3-235B-A22B-Instruct-2507"),  # 默认模型，会被 middleware 覆盖
            tools=self.get_tools(),  # 注册知识库查询相关工具
            middleware=[
                context_aware_prompt,  # 动态系统提示词
                inject_attachment_context,  # 附件上下文注入（LangChain 标准中间件）
                context_based_model,  # 动态模型选择
                dynamic_tool_middleware,  # 动态工具选择（支持 MCP 工具注册）
                ModelRetryMiddleware(),  # 模型重试中间件
            ],
            checkpointer=await self._get_checkpointer(),
        )

        self.graph = graph
        return graph

    async def process_messages_non_stream(self, messages: list[str], input_context=None, **kwargs):
        """非流式处理消息，等待完整响应后一次性返回"""
        context = self.context_schema.from_file(module_name=self.module_name, input_context=input_context)
        
        # 检查是否启用流式输出
        if getattr(context, 'streaming', False):
            # 如果启用了流式输出，回退到原有的流式方法
            async for msg, metadata in self.stream_messages(messages, input_context=input_context):
                # 如果不显示思考过程，过滤掉思考相关的消息
                if not getattr(context, 'show_thinking', False) and self._is_thinking_message(msg):
                    continue
                yield msg, metadata
            return
        
        # 使用 invoke 方法进行非流式处理
        result = await self.invoke_messages(messages, input_context=input_context)
        
        # 从结果中提取AI响应消息
        messages_list = result.get("messages", [])
        for msg in messages_list:
            if hasattr(msg, 'type') and msg.type == 'ai':
                # 如果不显示思考过程，检查是否为思考消息
                if not getattr(context, 'show_thinking', False) and self._is_thinking_message(msg):
                    continue
                # 返回AI消息和元数据
                yield msg, {"agent_id": self.id, "non_stream": True}

    def _is_thinking_message(self, msg) -> bool:
        """判断消息是否为思考过程消息"""
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            content = msg.content.lower()
            # 更严格的思考过程关键词检测，避免误判正常响应
            # 只有明确表示思考过程的短语才被过滤
            thinking_keywords = [
                'let me think step by step',
                'thinking process:',
                'my reasoning:',
                'let me analyze this step by step',
                'i will think through this',
                '思考过程：',
                '让我逐步思考：',
                '我的推理过程：',
                '逐步分析如下：'
            ]
            return any(keyword in content for keyword in thinking_keywords)
        return False

    async def stream_messages(self, messages: list[str], input_context=None, **kwargs):
        """重写流式消息处理方法，支持思考过程控制"""
        # 获取上下文配置
        context = self.context_schema.from_file(module_name=self.module_name, input_context=input_context)
        
        # 调用父类的流式处理方法
        async for msg, metadata in super().stream_messages(messages, input_context=input_context, **kwargs):
            # 如果不显示思考过程，过滤掉思考相关的消息
            if not getattr(context, 'show_thinking', False) and self._is_thinking_message(msg):
                continue
            yield msg, metadata


def main():
    pass


if __name__ == "__main__":
    main()
    # asyncio.run(main())