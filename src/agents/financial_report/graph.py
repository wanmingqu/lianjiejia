from langchain.agents import create_agent

from src import config
from src.agents.common import BaseAgent, get_mcp_tools, load_chat_model
from src.agents.common.middlewares import context_aware_prompt, context_based_model
from src.agents.financial_report.toolkits.financial import get_financial_tools
from src.utils import logger

_mcp_servers = {"mcp-server-chart": {"command": "npx", "args": ["-y", "@antv/mcp-server-chart"], "transport": "stdio"}}


class FinancialReportAgent(BaseAgent):
    name = "上市公司财报助手"
    description = "用于从上市公司财报 PDF 中提取关键财务报表（资产负债表/利润表/现金流量表）并辅助分析、生成图表的智能体。"
    capabilities = ["file_upload", "generate_charts"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def get_tools(self):
        chart_tools = await get_mcp_tools("mcp-server-chart", additional_servers=_mcp_servers)
        financial_tools = get_financial_tools()
        return chart_tools + financial_tools

    async def get_graph(self, **kwargs):
        if self.graph:
            return self.graph

        graph = create_agent(
            model=load_chat_model(config.default_model),
            tools=await self.get_tools(),
            middleware=[context_aware_prompt, context_based_model],
            checkpointer=await self._get_checkpointer(),
        )

        self.graph = graph
        logger.info("FinancialReportAgent 构建成功")
        return graph
