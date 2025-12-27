from typing import Annotated, Any
import re
import os
import json

from langchain.tools import tool
from pydantic import BaseModel, Field

from src.plugins.document_processor_factory import DocumentProcessorFactory
from src.utils import logger


class ProcessPDFModel(BaseModel):
    file_path: str = Field(description="要处理的 PDF 文件路径（服务器上的绝对路径或相对路径）", example="/data/files/600519_q1_report.pdf")
    processor_type: str | None = Field(default=None, description="使用的文档处理器类型，若不指定则使用环境变量或默认值")


class ExtractSectionsModel(BaseModel):
    file_path: str = Field(description="要处理的 PDF 文件路径（服务器上的绝对路径或相对路径）")
    processor_type: str | None = Field(default=None, description="使用的文档处理器类型，若不指定则使用环境变量或默认值")
    lang: str = Field(default="zh", description="文档语言，支持 'zh' 或 'en'")


@tool(name_or_callable="提取 PDF 文本", args_schema=ProcessPDFModel)
def process_financial_pdf(file_path: Annotated[str, "要处理的 PDF 文件路径（服务器上的绝对路径或相对路径）"], processor_type: Annotated[str | None, "处理器类型（可选）"] = None) -> str:
    """使用系统配置的文档处理器提取 PDF 的文本内容。

    这个工具用于将上传的上市公司财报 PDF 转换为可供模型分析的纯文本。
    """
    try:
        processor_type = processor_type or os.getenv("FIN_DOC_PROCESSOR") or "mineru_ocr"
        logger.info(f"Processing financial PDF: {file_path} with processor {processor_type}")
        text = DocumentProcessorFactory.process_file(processor_type, file_path, params=None)

        if not text:
            return "未能从文档中提取到任何文本，请检查文件或更换处理器。"

        # Limit returned text size to avoid extremely large payloads
        max_len = 20000
        if len(text) > max_len:
            logger.info(f"Extracted text length {len(text)} exceeds max {max_len}, truncating")
            return text[:max_len] + "\n\n...（文本被截断）"

        return text

    except Exception as e:
        logger.error(f"process_financial_pdf error: {e}")
        return f"从 PDF 提取文本失败: {e}" 


@tool(name_or_callable="提取财报重要章节", args_schema=ExtractSectionsModel)
def extract_financial_sections(file_path: Annotated[str, "要处理的 PDF 文件路径"], processor_type: Annotated[str | None, "处理器类型（可选）"] = None, lang: Annotated[str, "文档语言，'zh' 或 'en'"] = "zh") -> str:
    """从财报 PDF 中提取关键报表章节（比如资产负债表、利润表、现金流量表）并返回一个 JSON 字符串。

    说明：该工具使用简单的规则定位章节标题并截取对应文本段，便于后续由 LLM 进行结构化解析与数值识别。
    """
    try:
        # 先提取文本
        processor_type = processor_type or os.getenv("FIN_DOC_PROCESSOR") or "mineru_ocr"
        raw_text = DocumentProcessorFactory.process_file(processor_type, file_path, params=None)
        if not raw_text:
            return json.dumps({"error": "未能提取到文本"}, ensure_ascii=False)

        # 定义章节关键词
        if lang.startswith("zh"):
            sections_map = {
                "资产负债表": [r"资产负债表", r"资产与负债表"],
                "利润表": [r"利润表", r"损益表", r"综合收益表"],
                "现金流量表": [r"现金流量表", r"现金流量"],
                "母公司所有者权益变动表": [r"所有者权益变动表", r"股东权益变动表"],
            }
        else:
            sections_map = {
                "Balance Sheet": [r"Balance Sheet", r"Statement of Financial Position"],
                "Income Statement": [r"Income Statement", r"Statement of Profit"],
                "Cash Flow Statement": [r"Cash Flow Statement", r"Statement of Cash Flows"],
            }

        # Normalize text (simple)
        text = raw_text.replace("\r", "\n")

        # Find headings positions
        found = {}
        for name, patterns in sections_map.items():
            for p in patterns:
                match = re.search(p, text, flags=re.IGNORECASE)
                if match:
                    found[name] = match.start()
                    break

        # If none found, try coarse search using line-based scanning for keywords
        if not found:
            lines = text.splitlines()
            for i, line in enumerate(lines[:2000]):  # only scan first part
                for name, patterns in sections_map.items():
                    for p in patterns:
                        if re.search(p, line, flags=re.IGNORECASE):
                            # approximate position
                            pos = sum(len(l)+1 for l in lines[:i])
                            found[name] = pos
                            break

        if not found:
            return json.dumps({"error": "未在文档中识别到已知的财报章节，请提供更完整的 PDF 或尝试更换处理器"}, ensure_ascii=False)

        # Build sections by sorting positions and slicing
        items = sorted(found.items(), key=lambda x: x[1])
        sections = {}
        for idx, (name, pos) in enumerate(items):
            start = pos
            end = None
            if idx + 1 < len(items):
                end = items[idx + 1][1]
            else:
                end = start + 10000  # cap

            snippet = text[start:end]
            # Trim snippet
            snippet = snippet.strip()[:5000]
            sections[name] = snippet

        return json.dumps({"sections": sections}, ensure_ascii=False)

    except Exception as e:
        logger.error(f"extract_financial_sections error: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)



class ExtractTablesModel(BaseModel):
    file_path: str = Field(description="要处理的 PDF 文件路径（服务器上的绝对路径或相对路径）")
    processor_type: str | None = Field(default=None, description="使用的文档处理器类型，若不指定则使用环境变量或默认值")
    lang: str = Field(default="zh", description="文档语言，支持 'zh' 或 'en'")
    max_rows_per_section: int = Field(default=500, description="在每个章节中解析的最大表格行数，防止超大输出")


@tool(name_or_callable="结构化财报表格", args_schema=ExtractTablesModel)
def extract_financial_tables(file_path: Annotated[str, "要处理的 PDF 文件路径"], processor_type: Annotated[str | None, "处理器类型（可选）"] = None, lang: Annotated[str, "文档语言，'zh' 或 'en'"] = "zh", max_rows_per_section: Annotated[int, "最大行数（可选）"] = 500) -> str:
    """从财报 PDF 中提取并结构化表格数据，返回 JSON 字符串。

    该工具先定位关键章节（调用 extract_financial_sections），然后对每个章节中含有表格形式的行进行解析，尝试识别列头与科目-数值对，返回结构化数据，格式示例：
    {
      "sections": {
         "资产负债表": {
             "columns": ["科目", "本期数", "上年数"],
             "rows": [{"label": "总资产", "values": {"本期数": 100.0, "上年数": 90.0}}, ...]
         }, ...
      }
    }
    """
    try:
        # 获取章节文本（重用已有工具）
        sec_json = extract_financial_sections(file_path, processor_type=processor_type, lang=lang)
        sec_obj = json.loads(sec_json)
        if "error" in sec_obj:
            return json.dumps({"error": "无法提取章节: " + str(sec_obj.get("error"))}, ensure_ascii=False)

        sections = sec_obj.get("sections", {})

        def parse_number(token: str):
            # Normalize number like "(1,234.56)" => -1234.56, "12.3%" => 0.123 (keep as float), or "-" -> None
            if not token:
                return None
            s = token.strip()
            # handle parentheses as negative
            neg = False
            if s.startswith("(") and s.endswith(")"):
                neg = True
                s = s[1:-1]
            # strip percent
            is_percent = s.endswith("%")
            if is_percent:
                s = s[:-1]
            # remove commas
            s = s.replace(",", "")
            # remove any non numeric trailing chars
            s = re.sub(r"[^0-9.\-]", "", s)
            if s == "" or s == "-":
                return None
            try:
                val = float(s)
                if neg:
                    val = -val
                if is_percent:
                    val = val / 100.0
                return val
            except Exception:
                return None

        structured = {"sections": {}}

        for sec_name, snippet in sections.items():
            lines = [ln.rstrip() for ln in snippet.splitlines() if ln.strip()]
            if not lines:
                continue

            # Try to detect unit first (e.g., "单位：元" or "单位：人民币元")
            unit = None
            for i, ln in enumerate(lines[:5]):
                m = re.search(r"单位[:：]\s*([^\s，,]+)", ln)
                if m:
                    unit = m.group(1)
                    # remove this line from lines to avoid confusing header detection
                    lines.pop(i)
                    break

            # find header line (prefer one that contains year like 2024 or tokens like 本期数)
            header_line = None
            header_index = None
            for i, ln in enumerate(lines[:20]):
                if re.search(r"\b(20\d{2}|19\d{2})年?\b", ln) or re.search(r"本期数|上年数|上年同期数|本期金额|期末数", ln):
                    header_line = ln
                    header_index = i
                    break
                # also consider lines with 2+ non-label tokens (heuristic)
                count_numbers = len(re.findall(r"[\d\(\)\-]+[\d,\.\)]*%?", ln))
                if count_numbers >= 2:
                    header_line = ln
                    header_index = i
                    break

            columns = []
            rows = []

            if header_line:
                # split header into tokens by multiple spaces or tabs
                header_tokens = re.split(r"\s{2,}|\t", header_line)
                if len(header_tokens) < 2:
                    header_tokens = header_line.split()
                columns = [t.strip() for t in header_tokens if t.strip()]
                # interpret columns as periods
                periods = columns[:]
                # remove header and leading lines up to header from content
                content_lines = lines[header_index + 1 :]
            else:
                # no clear header, try to infer columns from first numeric line
                content_lines = lines
                periods = []

            # If header contains year tokens like 2024, normalize to '2024' or '2024年'
            periods = [re.sub(r"年$", "", p) if re.search(r"\b(20\d{2}|19\d{2})年?\b", p) else p for p in periods]

            # parse content lines into label and numbers
            for ln in content_lines[:max_rows_per_section]:
                # skip lines that look like subheaders
                if re.match(r"^(-+|=+)$", ln):
                    continue

                # find all number tokens in the line
                num_tokens = re.findall(r"\(?-?[0-9][0-9,\.\(\)\%\-]*\)?", ln)
                if not num_tokens:
                    continue
                # extract label by removing numeric tokens from the end
                split_at = None
                m = re.search(r"\(?-?[0-9]", ln)
                if m:
                    split_at = m.start()
                if split_at is not None and split_at > 0:
                    label = ln[:split_at].strip()
                else:
                    label = " ".join(ln.split()[:2])

                values = []
                for tok in num_tokens:
                    parsed = parse_number(tok)
                    values.append(parsed)

                # map values to periods
                val_map = {}
                if periods and len(periods) == len(values):
                    for col, v in zip(periods, values):
                        val_map[col] = v
                elif periods and len(values) > 0:
                    # align right
                    for idx, v in enumerate(reversed(values)):
                        col_idx = len(periods) - 1 - idx
                        if col_idx >= 0:
                            val_map[periods[col_idx]] = v
                else:
                    for idx, v in enumerate(values):
                        val_map[str(idx)] = v

                rows.append({"label": label, "values": val_map})

            structured["sections"][sec_name] = {"unit": unit, "periods": periods, "rows": rows}

        return json.dumps(structured, ensure_ascii=False)

    except Exception as e:
        logger.error(f"extract_financial_tables error: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


from .analysis import compute_yoy, compute_qoq, compute_ratios, timeseries_from_rows
from .chart import generate_chart_payload
from pydantic import BaseModel, Field
from typing import List


class GenerateChartModel(BaseModel):
    section: str = Field(description="要绘图的章节名，例如 '资产负债表' 或 '利润表'")
    period_keys: List[str] = Field(description="按顺序的期次列表，例如 ['2022','2023','2024']")
    top_n: int = Field(default=5, description="展示的最高 N 项")


@tool(name_or_callable="生成财务趋势图", args_schema=GenerateChartModel)
def generate_financial_chart(section: Annotated[str, "章节名"], period_keys: Annotated[List[str], "Period keys"], top_n: Annotated[int, "Top N"] = 5) -> str:
    """Generate a chart payload for a given section by aggregating rows and calling chart payload generator.

    Note: This tool expects that the agent provides the parsed `sections` data (e.g., from `extract_financial_tables`).
    For convenience, callers can implement a prompt flow like: 1) call `extract_financial_tables` 2) pass the resulting `sections[section]['rows']` and `period_keys` into this tool.
    """
    try:
        # This simplified tool cannot reach into the agent's memory; it expects the agent passes in the section rows as a JSON string in a special convention.
        # For now, return a template indicating required inputs so LLMs can call the right tools.
        payload_template = {
            "required_inputs": ["rows_json", "period_keys"],
            "usage": "调用流程: 先运行 extract_financial_tables 获取 sections，再将 sections['" + section + "']['rows'] 作为 rows_json，传入 top_n 与 period_keys 调用此工具。",
            "example": {"rows_json_example": [{"label": "营业收入", "values": {period_keys[-2]: 1800, period_keys[-1]: 2000}}], "period_keys": period_keys, "top_n": top_n},
        }
        return json.dumps(payload_template, ensure_ascii=False)
    except Exception as e:
        logger.error(f"generate_financial_chart error: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def get_financial_tools() -> list[Any]:
    """返回给智能体使用的金融文档相关工具列表"""
    return [process_financial_pdf, extract_financial_sections, extract_financial_tables, generate_financial_chart]
