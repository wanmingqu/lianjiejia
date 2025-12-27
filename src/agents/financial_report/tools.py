"""财报分析Agent专用工具"""

import re
import json
import uuid
import requests
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from langchain.tools import tool
from src.storage.minio import aupload_file_to_minio
from src.utils import logger


def _extract_from_text(text_content: str, metrics: List[str]) -> Dict[str, Any]:
    """从文本中提取财务数据"""
    extracted = {}
    
    # 定义中文关键词映射
    keyword_map = {
        "revenue": ["营业收入", "主营业务收入", "收入", "营收"],
        "net_profit": ["净利润", "净收益", "净利润额"],
        "total_assets": ["总资产", "资产总计", "资产合计"],
        "total_liabilities": ["总负债", "负债总计", "负债合计"],
        "current_assets": ["流动资产", "流动资产合计"],
        "current_liabilities": ["流动负债", "流动负债合计"],
        "total_equity": ["所有者权益", "股东权益", "净资产"]
    }
    
    for metric in metrics:
        keywords = keyword_map.get(metric, [metric])
        for keyword in keywords:
            # 使用正则表达式查找数字
            pattern = rf"{keyword}[：:]\s*([0-9,，.]+)"
            matches = re.findall(pattern, text_content)
            if matches:
                # 清理并转换数字
                number_str = matches[0].replace(',', '').replace('，', '')
                try:
                    extracted[metric] = float(number_str)
                    break
                except ValueError:
                    continue
    
    return extracted


def _extract_from_tables(tables: List[Dict], metrics: List[str]) -> Dict[str, Any]:
    """从表格中提取财务数据"""
    extracted = {}
    
    # 定义中文关键词映射
    keyword_map = {
        "revenue": ["营业收入", "主营业务收入", "收入", "营收"],
        "net_profit": ["净利润", "净收益", "净利润额"],
        "total_assets": ["总资产", "资产总计", "资产合计"],
        "total_liabilities": ["总负债", "负债总计", "负债合计"],
        "current_assets": ["流动资产", "流动资产合计"],
        "current_liabilities": ["流动负债", "流动负债合计"],
        "total_equity": ["所有者权益", "股东权益", "净资产"]
    }
    
    for table in tables:
        if "data" not in table or "columns" not in table:
            continue
            
        df_data = table["data"]
        columns = table["columns"]
        
        # 查找项目和金额列
        item_col = None
        amount_col = None
        
        for i, col in enumerate(columns):
            col_lower = col.lower()
            if any(keyword in col for keyword in ["项目", "名称", "科目"]):
                item_col = i
            elif any(keyword in col for keyword in ["金额", "数值", "数额", "万元", "元"]):
                amount_col = i
        
        if item_col is not None and amount_col is not None:
            # 处理字典格式的数据
            if df_data and isinstance(df_data[0], dict):
                # 新格式：字典列表
                for row_dict in df_data:
                    item_name = str(row_dict.get(columns[item_col], "")).strip()
                    amount_str = str(row_dict.get(columns[amount_col], "")).strip()
                    
                    for metric, keywords in keyword_map.items():
                        if any(keyword in item_name for keyword in keywords):
                            # 清理并转换数字（处理逗号分隔）
                            # 如果包含逗号，先处理逗号
                            clean_amount = amount_str.replace(',', '').replace('，', '')
                            number_str = re.sub(r'[^\d.]', '', clean_amount)
                            
                            try:
                                if number_str:
                                    extracted[metric] = float(number_str)
                                    logger.debug(f"成功提取 {metric}: {amount_str} -> {float(number_str)}")
                            except ValueError:
                                # 尝试更宽松的数字解析
                                try:
                                    # 提取所有数字字符
                                    digits = re.findall(r'\d+\.?\d*', amount_str)
                                    if digits:
                                        extracted[metric] = float(digits[0])
                                        logger.debug(f"宽松解析成功 {metric}: {amount_str} -> {float(digits[0])}")
                                except (ValueError, IndexError):
                                    pass
                            break
            else:
                # 旧格式：列表格式（向后兼容）
                for row in df_data:
                    if len(row) > max(item_col, amount_col):
                        item_name = str(row[item_col]).strip()
                        amount_str = str(row[amount_col]).strip()
                        
                        for metric, keywords in keyword_map.items():
                            if any(keyword in item_name for keyword in keywords):
                                # 清理并转换数字（处理逗号分隔）
                                # 如果包含逗号，先处理逗号
                                clean_amount = amount_str.replace(',', '').replace('，', '')
                                number_str = re.sub(r'[^\d.]', '', clean_amount)
                                
                                try:
                                    if number_str:
                                        extracted[metric] = float(number_str)
                                        logger.debug(f"成功提取 {metric}: {amount_str} -> {float(number_str)}")
                                except ValueError:
                                    # 尝试更宽松的数字解析
                                    try:
                                        # 提取所有数字字符
                                        digits = re.findall(r'\d+\.?\d*', amount_str)
                                        if digits:
                                            extracted[metric] = float(digits[0])
                                            logger.debug(f"宽松解析成功 {metric}: {amount_str} -> {float(digits[0])}")
                                    except (ValueError, IndexError):
                                        pass
                                break
    
    return extracted





@tool(name_or_callable="parse_uploaded_financial_pdf", description="解析用户上传的财务报表PDF文件，提取文本和表格数据")
def parse_uploaded_financial_pdf(markdown_content: str, extract_tables: bool = True, extract_text: bool = True) -> Dict[str, Any]:
    """
    解析用户上传的财务报表PDF文件
    
    Args:
        markdown_content: 上传PDF文件转换后的markdown内容
        extract_tables: 是否提取表格数据
        extract_text: 是否提取文本数据
    
    Returns:
        Dict: 解析结果包含文本和表格数据
    """
    try:
        # 从markdown内容中解析表格和文本
        tables = []
        text_content = markdown_content
        
        result = {
            "status": "success",
            "text_content": "",
            "tables": [],
            "metadata": {
                "file_size": len(pdf_data),
                "pages_processed": 0
            }
        }
        
        # 尝试使用PyPDF2或pdfplumber解析PDF
        try:
            import PyPDF2
            import pdfplumber
            
            with pdfplumber.open(tmp_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    if extract_text:
                        text = page.extract_text()
                        if text:
                            result["text_content"] += f"\n--- 第{page_num + 1}页 ---\n{text}\n"
                    
                    if extract_tables:
                        tables = page.extract_tables()
                        for table in tables:
                            if table and len(table) > 1:
                                # 清理表格数据
                                clean_table = []
                                for row in table:
                                    clean_row = [str(cell).strip() if cell else "" for cell in row]
                                    if any(clean_row):  # 过滤空行
                                        clean_table.append(clean_row)
                                
                                if clean_table:
                                    df = pd.DataFrame(clean_table[1:], columns=clean_table[0])
                                    result["tables"].append({
                                        "page": page_num + 1,
                                        "data": df.to_dict('records'),
                                        "columns": clean_table[0]
                                    })
                
                result["metadata"]["pages_processed"] = len(pdf.pages)
            
        except ImportError:
            # 如果没有安装PDF解析库，返回模拟数据
            logger.warning("未安装PDF解析库，返回模拟数据")
            result["status"] = "warning"
            result["message"] = "未安装PDF解析库，返回模拟数据"
            
            # 模拟一些财务数据
            result["text_content"] = """
            模拟财务报表内容
            
            资产负债表（单位：万元）
            资产:
            流动资产: 10000
            非流动资产: 20000
            总资产: 30000
            
            负债和所有者权益:
            流动负债: 5000
            非流动负债: 8000
            负债合计: 13000
            所有者权益: 17000
            负债和所有者权益总计: 30000
            
            利润表（单位：万元）
            营业收入: 15000
            营业成本: 10000
            营业利润: 3000
            净利润: 2500
            """
            
            # 模拟表格数据
            result["tables"] = [
                {
                    "page": 1,
                    "data": [
                        {"项目": "流动资产", "金额": "10000"},
                        {"项目": "非流动资产", "金额": "20000"},
                        {"项目": "总资产", "金额": "30000"}
                    ],
                    "columns": ["项目", "金额"]
                }
            ]
        
        finally:
            # 清理临时文件
            os.unlink(tmp_path)
        
        logger.info(f"PDF解析完成: 处理{result['metadata']['pages_processed']}页，提取{len(result['tables'])}个表格")
        return result
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "message": "PDF解析失败"
        }
        logger.error(f"PDF解析失败: {e}")
        return error_result


@tool(name_or_callable="process_uploaded_financial_file", description="处理用户上传的财务报表文件（PDF、Excel等），提取财务数据")
def process_uploaded_financial_file(
    file_content: str, 
    file_name: str = "",
    file_type: str = "pdf",
    extract_tables: bool = True, 
    extract_text: bool = True
) -> Dict[str, Any]:
    """
    处理用户上传的财务报表文件
    
    Args:
        file_content: 文件内容的markdown格式（已通过系统转换）
        file_name: 原始文件名
        file_type: 文件类型（pdf、xlsx、docx等）
        extract_tables: 是否提取表格数据
        extract_text: 是否提取文本数据
    
    Returns:
        Dict: 解析结果包含文本和表格数据
    """
    try:
        logger.info(f"开始处理上传的财务文件: {file_name}")
        
        # 解析markdown内容中的表格和文本
        tables = []
        text_content = file_content
        
        # 从markdown中提取表格
        import re
        table_pattern = r'(\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)*)'
        table_matches = re.findall(table_pattern, file_content)
        
        for i, table_text in enumerate(table_matches):
            lines = table_text.strip().split('\n')
            if len(lines) >= 3:
                # 解析表头
                header_line = lines[0].strip()
                columns = [col.strip() for col in header_line.split('|')[1:-1]]
                
                # 跳过分隔行
                data_lines = lines[2:]
                
                # 解析数据行
                data = []
                for data_line in data_lines:
                    if data_line.strip():
                        row_data = [cell.strip() for cell in data_line.split('|')[1:-1]]
                        if row_data:
                            data.append(row_data)
                
                if data:
                    # 转换为字典格式以便后续处理
                    dict_data = []
                    for row in data:
                        row_dict = {}
                        for j, value in enumerate(row):
                            if j < len(columns):
                                row_dict[columns[j]] = value
                        dict_data.append(row_dict)
                    
                    tables.append({
                        "table_id": i + 1,
                        "columns": columns,
                        "data": dict_data,
                        "raw_data": data,
                        "row_count": len(data),
                        "col_count": len(columns)
                    })
        
        # 清理文本内容（移除表格部分，保留其他文本）
        clean_text = file_content
        for table_text in table_matches:
            clean_text = clean_text.replace(table_text, "\n[表格数据已提取]\n")
        
        # 如果没有提取到表格，尝试从文本中提取财务数据
        if not tables and extract_text:
            logger.info("未从markdown中提取到表格，尝试从文本解析财务数据")
            # 这里可以添加更多的文本解析逻辑
        
        result = {
            "text_content": clean_text if extract_text else "",
            "tables": tables if extract_tables else [],
            "table_count": len(tables),
            "file_name": file_name,
            "file_type": file_type,
            "status": "success",
            "message": f"成功处理文件 {file_name}，提取到 {len(tables)} 个表格"
        }
        
        logger.info(f"文件处理完成: {result['message']}")
        return result
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "message": f"文件处理失败: {file_name}",
            "text_content": "",
            "tables": [],
            "table_count": 0
        }
        logger.error(f"上传文件处理失败: {e}")
        return error_result


@tool(name_or_callable="extract_financial_data", description="从解析的财务数据中提取关键财务指标")
def extract_financial_data(
    text_content: str = "",
    tables: List[Dict] = None,
    metrics: List[str] = None
) -> Dict[str, Any]:
    """
    提取关键财务指标
    
    Args:
        text_content: PDF解析的文本内容
        tables: PDF解析的表格数据
        metrics: 需要提取的财务指标列表
    
    Returns:
        Dict: 提取的财务数据
    """
    try:
        if tables is None:
            tables = []
        if metrics is None:
            metrics = ["revenue", "net_profit", "total_assets", "total_liabilities"]
        
        financial_data = {
            "status": "success",
            "extracted_metrics": {},
            "raw_data": {},
            "confidence_scores": {}
        }
        
        # 从文本中提取财务数据
        text_data = _extract_from_text(text_content, metrics)
        financial_data["raw_data"]["text_extracted"] = text_data
        
        # 从表格中提取财务数据
        table_data = _extract_from_tables(tables, metrics)
        financial_data["raw_data"]["table_extracted"] = table_data
        
        # 合并和标准化数据
        for metric in metrics:
            value = None
            confidence = 0.0
            
            # 优先使用表格数据
            if metric in table_data and table_data[metric]:
                value = table_data[metric]
                confidence += 0.7
            
            # 补充文本数据
            if metric in text_data and text_data[metric]:
                if value is None:
                    value = text_data[metric]
                    confidence += 0.3
                else:
                    # 如果两个来源都有数据，选择更合理的
                    confidence = 0.9
            
            financial_data["extracted_metrics"][metric] = value
            financial_data["confidence_scores"][metric] = confidence
        
        logger.info(f"财务数据提取完成: 提取{len(financial_data['extracted_metrics'])}个指标")
        return financial_data
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "message": "财务数据提取失败"
        }
        logger.error(f"财务数据提取失败: {e}")
        return error_result


@tool(name_or_callable="calculate_financial_ratios", description="计算各类财务比率指标")
def calculate_financial_ratios(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算财务比率
    
    Args:
        financial_data: 包含财务指标的字典
    
    Returns:
        Dict: 计算的财务比率
    """
    try:
        ratios = {
            "status": "success",
            "profitability_ratios": {},
            "solvency_ratios": {},
            "operational_ratios": {},
            "growth_ratios": {}
        }
        
        metrics = financial_data.get("extracted_metrics", {})
        
        # 盈利能力比率
        if "net_profit" in metrics and "total_assets" in metrics and metrics["total_assets"] != 0:
            roa = (metrics["net_profit"] / metrics["total_assets"]) * 100
            ratios["profitability_ratios"]["roa"] = round(roa, 2)
        
        if "net_profit" in metrics and "total_equity" in metrics and metrics["total_equity"] != 0:
            roe = (metrics["net_profit"] / metrics["total_equity"]) * 100
            ratios["profitability_ratios"]["roe"] = round(roe, 2)
        
        if "revenue" in metrics and "net_profit" in metrics and metrics["revenue"] != 0:
            net_profit_margin = (metrics["net_profit"] / metrics["revenue"]) * 100
            ratios["profitability_ratios"]["net_profit_margin"] = round(net_profit_margin, 2)
        
        # 偿债能力比率
        if "current_assets" in metrics and "current_liabilities" in metrics and metrics["current_liabilities"] != 0:
            current_ratio = metrics["current_assets"] / metrics["current_liabilities"]
            ratios["solvency_ratios"]["current_ratio"] = round(current_ratio, 2)
        
        if "total_liabilities" in metrics and "total_assets" in metrics and metrics["total_assets"] != 0:
            debt_ratio = (metrics["total_liabilities"] / metrics["total_assets"]) * 100
            ratios["solvency_ratios"]["debt_ratio"] = round(debt_ratio, 2)
        
        # 运营能力比率
        if "revenue" in metrics and "total_assets" in metrics and metrics["total_assets"] != 0:
            asset_turnover = metrics["revenue"] / metrics["total_assets"]
            ratios["operational_ratios"]["asset_turnover"] = round(asset_turnover, 2)
        
        logger.info(f"财务比率计算完成: 计算了{len(ratios['profitability_ratios'])}个盈利比率，{len(ratios['solvency_ratios'])}个偿债比率")
        return ratios
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "message": "财务比率计算失败"
        }
        logger.error(f"财务比率计算失败: {e}")
        return error_result





@tool(name_or_callable="generate_financial_report", description="生成完整的财务分析报告")
def generate_financial_report(
    financial_data: Dict[str, Any],
    ratios: Dict[str, Any] = None,
    charts: List[Dict] = None,
    analysis_dimensions: List[str] = None
) -> Dict[str, Any]:
    """
    生成财务分析报告
    
    Args:
        financial_data: 财务数据
        ratios: 财务比率
        charts: 图表数据
        analysis_dimensions: 分析维度
    
    Returns:
        Dict: 生成的财务分析报告
    """
    try:
        if analysis_dimensions is None:
            analysis_dimensions = ["profitability", "solvency"]
        if ratios is None:
            ratios = {}
        if charts is None:
            charts = []
        
        metrics = financial_data.get("extracted_metrics", {})
        
        # 中文指标名称映射
        name_map = {
            "revenue": "营业收入",
            "net_profit": "净利润",
            "total_assets": "总资产",
            "total_liabilities": "总负债",
            "current_assets": "流动资产",
            "current_liabilities": "流动负债",
            "total_equity": "所有者权益"
        }
        
        report = {
            "status": "success",
            "report_content": "",
            "executive_summary": "",
            "detailed_analysis": {},
            "recommendations": []
        }
        
        # 生成报告内容
        report_content = "# 财务分析报告\n\n"
        
        # 执行摘要
        executive_summary = "## 执行摘要\n\n"
        executive_summary += "本报告基于提供的财务报表数据，对公司财务状况进行全面分析。\n\n"
        
        # 主要财务数据
        report_content += "## 主要财务数据\n\n"
        report_content += "| 财务指标 | 金额（万元） |\n"
        report_content += "|---------|------------|\n"
        
        for metric, value in metrics.items():
            if value is not None:
                chinese_name = name_map.get(metric, metric)
                report_content += f"| {chinese_name} | {value:,.2f} |\n"
        
        report_content += "\n"
        
        # 盈利能力分析
        if "profitability" in analysis_dimensions and ratios.get("profitability_ratios"):
            profitability = ratios["profitability_ratios"]
            report_content += "## 盈利能力分析\n\n"
            
            if "roe" in profitability:
                roe = profitability["roe"]
                if roe > 15:
                    assessment = "优秀"
                elif roe > 10:
                    assessment = "良好"
                else:
                    assessment = "一般"
                report_content += f"### 净资产收益率(ROE)\n净资产收益率为{roe}%，表现为{assessment}。\n\n"
            
            if "net_profit_margin" in profitability:
                margin = profitability["net_profit_margin"]
                report_content += f"### 净利率\n净利率为{margin}%，显示公司的盈利能力。\n\n"
        
        # 偿债能力分析
        if "solvency" in analysis_dimensions and ratios.get("solvency_ratios"):
            solvency = ratios["solvency_ratios"]
            report_content += "## 偿债能力分析\n\n"
            
            if "current_ratio" in solvency:
                current = solvency["current_ratio"]
                if current > 2:
                    assessment = "强"
                elif current > 1:
                    assessment = "中等"
                else:
                    assessment = "弱"
                report_content += f"### 流动比率\n流动比率为{current}，短期偿债能力{assessment}。\n\n"
            
            if "debt_ratio" in solvency:
                debt = solvency["debt_ratio"]
                if debt < 40:
                    assessment = "低"
                elif debt < 60:
                    assessment = "中等"
                else:
                    assessment = "高"
                report_content += f"### 资产负债率\n资产负债率为{debt}%，财务风险{assessment}。\n\n"
        
        # 图表展示
        if charts:
            report_content += "## 财务图表\n\n"
            for i, chart in enumerate(charts, 1):
                report_content += f"![图表{i}]({chart['url']})\n\n"
        
        # 风险提示和建议
        report_content += "## 风险提示和建议\n\n"
        recommendations = []
        
        # 基于数据生成建议
        if "total_liabilities" in metrics and "total_assets" in metrics:
            debt_ratio = (metrics["total_liabilities"] / metrics["total_assets"]) * 100
            if debt_ratio > 70:
                recommendations.append("建议关注负债水平，考虑降低财务杠杆")
        
        if "current_assets" in metrics and "current_liabilities" in metrics:
            current_ratio = metrics["current_assets"] / metrics["current_liabilities"]
            if current_ratio < 1:
                recommendations.append("短期偿债压力较大，建议加强流动性管理")
        
        if not recommendations:
            recommendations.append("整体财务状况良好，建议保持现有经营策略")
        
        for rec in recommendations:
            report_content += f"- {rec}\n"
        
        report["report_content"] = report_content
        report["executive_summary"] = executive_summary
        report["recommendations"] = recommendations
        
        logger.info(f"财务报告生成完成: 包含{len(recommendations)}条建议")
        return report
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "message": "财务报告生成失败"
        }
        logger.error(f"财务报告生成失败: {e}")
        return error_result


@tool(name_or_callable="display_chart_image", description="正确显示图表图片，生成正确的Markdown格式")
async def display_chart_image(chart_url: str, title: str = "财务分析图表") -> str:
    """
    正确显示图表图片，生成正确的Markdown格式
    
    Args:
        chart_url: 图表URL
        title: 图表标题
    
    Returns:
        str: 正确的Markdown图片格式
    """
    try:
        # 确保URL是有效的
        if not chart_url or not isinstance(chart_url, str):
            return "图片URL无效"
        
        # 生成正确的Markdown格式
        markdown_image = f"![{title}]({chart_url})"
        
        logger.info(f"生成图表Markdown: {markdown_image}")
        return markdown_image
        
    except Exception as e:
        logger.error(f"生成图表Markdown失败: {e}")
        return f"![图表加载失败](https://via.placeholder.com/400x300?text=Chart+Error)"


@tool(name_or_callable="download_and_upload_chart", description="将外部图表URL下载并上传到本地MinIO存储，确保图片可正常显示")
async def download_and_upload_chart(chart_url: str, title: str = "财务分析图表") -> str:
    """
    将外部图表URL下载并上传到本地MinIO存储
    
    Args:
        chart_url: 外部图表URL（如支付宝OSS）
        title: 图表标题
    
    Returns:
        str: 本地MinIO图片URL，确保可正常显示
    """
    try:
        import requests
        
        logger.info(f"开始下载外部图表: {chart_url}")
        
        # 下载图片
        response = requests.get(chart_url, timeout=30)
        response.raise_for_status()
        
        # 获取文件扩展名
        content_type = response.headers.get('content-type', 'image/png')
        if 'jpeg' in content_type:
            ext = 'jpg'
        elif 'png' in content_type:
            ext = 'png'
        elif 'svg' in content_type:
            ext = 'svg'
        elif 'gif' in content_type:
            ext = 'gif'
        else:
            ext = 'png'  # 默认
        
        # 生成文件名
        file_name = f"financial_chart_{uuid.uuid4()}.{ext}"
        
        # 上传到MinIO
        local_url = await aupload_file_to_minio(
            bucket_name="generated-images",
            file_name=file_name,
            data=response.content,
            file_extension=ext
        )
        
        logger.info(f"图表已成功上传到本地MinIO: {local_url}")
        logger.info(f"原URL: {chart_url}")
        logger.info(f"新URL: {local_url}")
        
        return local_url
        
    except Exception as e:
        logger.error(f"下载上传图表失败: {e}")
        # 如果失败，返回原URL
        return chart_url


@tool(name_or_callable="generate_chart_image", description="将图表数据转换为可显示的图片URL")
async def generate_chart_image(
    chart_data: str,
    chart_type: str = "bar",
    title: str = "财务分析图表"
) -> str:
    """
    将图表数据转换为可显示的图片URL
    
    Args:
        chart_data: 图表数据（可能是base64、URL或其他格式）
        chart_type: 图表类型
        title: 图表标题
    
    Returns:
        str: 可显示的图片URL
    """
    try:
        # 如果chart_data已经是HTTP URL，下载并上传到本地
        if isinstance(chart_data, str) and chart_data.startswith('http'):
            # 如果是外部URL，下载到本地MinIO
            if any(domain in chart_data for domain in ['mdn.alipayobjects.com', 'feishu.cn', 'larksuite.com']):
                return await download_and_upload_chart(chart_data, title)
            else:
                return chart_data
        
        # 如果是base64数据，需要上传到MinIO
        if isinstance(chart_data, str) and chart_data.startswith('data:image'):
            # 提取base64数据
            import base64
            header, encoded = chart_data.split(',', 1)
            image_data = base64.b64decode(encoded)
            
            # 上传到MinIO
            file_name = f"chart_{uuid.uuid4()}.png"
            image_url = await aupload_file_to_minio(
                bucket_name="generated-images", 
                file_name=file_name, 
                data=image_data, 
                file_extension="png"
            )
            logger.info(f"图表已上传到MinIO: {image_url}")
            return image_url
        
        # 如果是其他格式的数据，尝试处理
        if isinstance(chart_data, str):
            # 可能是SVG格式
            if chart_data.strip().startswith('<svg'):
                # 将SVG转换为PNG并上传
                try:
                    import cairosvg
                    png_data = cairosvg.svg2png(bytestring=chart_data.encode())
                    
                    file_name = f"chart_{uuid.uuid4()}.png"
                    image_url = await aupload_file_to_minio(
                        bucket_name="generated-images", 
                        file_name=file_name, 
                        data=png_data, 
                        file_extension="png"
                    )
                    logger.info(f"SVG图表已转换并上传: {image_url}")
                    return image_url
                except ImportError:
                    logger.warning("未安装cairosvg，无法处理SVG格式")
                    return chart_data
            elif chart_data.strip().startswith('<?xml') or '<svg' in chart_data:
                # 尝试将XML格式的SVG处理
                try:
                    import cairosvg
                    png_data = cairosvg.svg2png(bytestring=chart_data.encode())
                    
                    file_name = f"chart_{uuid.uuid4()}.png"
                    image_url = await aupload_file_to_minio(
                        bucket_name="generated-images", 
                        file_name=file_name, 
                        data=png_data, 
                        file_extension="png"
                    )
                    logger.info(f"XML SVG图表已转换并上传: {image_url}")
                    return image_url
                except (ImportError, Exception):
                    logger.warning("SVG转换失败，返回原始数据")
                    return chart_data
        
        # 如果都无法处理，返回原始数据
        logger.warning(f"无法处理的图表数据格式: {type(chart_data)}")
        return str(chart_data)
        
    except Exception as e:
        logger.error(f"图表处理失败: {e}")
        return f"图表处理失败: {str(e)}"


def get_tools() -> List[Any]:
    """获取所有可运行的工具（给大模型使用）"""
    tools = [
        process_uploaded_financial_file,
        extract_financial_data,
        calculate_financial_ratios,
        display_chart_image,
        generate_chart_image,
        generate_financial_report,
    ]
    
    try:
        # 导入并添加通用工具
        from src.agents.common import get_buildin_tools
        tools.extend(get_buildin_tools())
        
    except Exception as e:
        logger.error(f"添加通用工具失败: {e}")
    
    return tools


def get_available_tools() -> List[Dict[str, Any]]:
    """获取可用工具信息（用于配置界面）"""
    tools_info = [
        {
            "name": "process_uploaded_financial_file",
            "description": "处理用户上传的财务报表文件（PDF、Excel等），提取财务数据",
            "type": "file_processor"
        },
        {
            "name": "extract_financial_data",
            "description": "从解析的财务数据中提取关键财务指标",
            "type": "data_extractor"
        },
        {
            "name": "calculate_financial_ratios",
            "description": "计算各类财务比率指标",
            "type": "calculator"
        },
        {
            "name": "generate_chart_image",
            "description": "将图表数据转换为可显示的图片URL",
            "type": "image_processor"
        },
        {
            "name": "generate_financial_report",
            "description": "生成完整的财务分析报告",
            "type": "report_generator"
        }
    ]
    
    try:
        # 添加通用工具信息
        from src.agents.common import gen_tool_info, get_buildin_tools
        buildin_tools = get_buildin_tools()
        tools_info.extend(gen_tool_info(buildin_tools))
        
    except Exception as e:
        logger.error(f"获取通用工具信息失败: {e}")
    
    return tools_info