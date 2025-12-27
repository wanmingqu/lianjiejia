#!/usr/bin/env python3
"""测试FinancialReportAgent功能"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, '/workspace')

from src.agents.financial_report.tools import (
    extract_financial_data,
    calculate_financial_ratios,
    generate_financial_charts,
    generate_financial_report
)


async def test_financial_analysis():
    """测试财报分析功能"""
    print("=== 测试FinancialReportAgent功能 ===\n")
    
    # 模拟财务数据
    sample_text = """
    某公司2023年度财务报表
    
    资产负债表（单位：万元）
    流动资产: 15000
    非流动资产: 25000
    总资产: 40000
    
    流动负债: 6000
    非流动负债: 10000
    总负债: 16000
    所有者权益: 24000
    
    利润表（单位：万元）
    营业收入: 20000
    营业成本: 12000
    营业利润: 5000
    净利润: 4000
    """
    
    sample_tables = [
        {
            "page": 1,
            "data": [
                {"项目": "流动资产", "金额": "15000"},
                {"项目": "非流动资产", "金额": "25000"},
                {"项目": "总资产", "金额": "40000"},
                {"项目": "流动负债", "金额": "6000"},
                {"项目": "非流动负债", "金额": "10000"},
                {"项目": "总负债", "金额": "16000"},
                {"项目": "所有者权益", "金额": "24000"}
            ],
            "columns": ["项目", "金额"]
        }
    ]
    
    # 1. 测试财务数据提取
    print("1. 测试财务数据提取...")
    extract_result = extract_financial_data.invoke({
        "text_content": sample_text,
        "tables": sample_tables,
        "metrics": ["revenue", "net_profit", "total_assets", "total_liabilities", "current_assets", "current_liabilities", "total_equity"]
    })
    
    if extract_result.get("status") == "success":
        print("✅ 数据提取成功")
        metrics = extract_result.get("extracted_metrics", {})
        for metric, value in metrics.items():
            if value is not None:
                print(f"  {metric}: {value:,.0f} 万元")
    else:
        print(f"❌ 数据提取失败: {extract_result.get('message')}")
        return
    
    # 2. 测试财务比率计算
    print("\n2. 测试财务比率计算...")
    ratios_result = calculate_financial_ratios.invoke({"financial_data": extract_result})
    
    if ratios_result.get("status") == "success":
        print("✅ 财务比率计算成功")
        
        # 盈利能力比率
        profitability = ratios_result.get("profitability_ratios", {})
        if profitability:
            print("  盈利能力:")
            for ratio, value in profitability.items():
                print(f"    {ratio}: {value}%")
        
        # 偿债能力比率
        solvency = ratios_result.get("solvency_ratios", {})
        if solvency:
            print("  偿债能力:")
            for ratio, value in solvency.items():
                print(f"    {ratio}: {value}")
    else:
        print(f"❌ 财务比率计算失败: {ratios_result.get('message')}")
        return
    
    # 3. 测试图表生成
    print("\n3. 测试图表生成...")
    charts_result = generate_financial_charts.invoke({
        "financial_data": extract_result,
        "chart_type": "bar",
        "chart_theme": "professional",
        "chart_size": "medium",
        "metrics": ["revenue", "net_profit", "total_assets"]
    })
    
    if charts_result.get("status") == "success":
        charts = charts_result.get("charts", [])
        print(f"✅ 图表生成成功: {len(charts)} 个图表")
        for chart in charts:
            print(f"  - {chart['type']}: {chart['title']}")
    else:
        print(f"❌ 图表生成失败: {charts_result.get('message')}")
        return
    
    # 4. 测试报告生成
    print("\n4. 测试报告生成...")
    report_result = generate_financial_report.invoke({
        "financial_data": extract_result,
        "ratios": ratios_result,
        "charts": charts,
        "analysis_dimensions": ["profitability", "solvency"]
    })
    
    if report_result.get("status") == "success":
        print("✅ 财务报告生成成功")
        recommendations = report_result.get("recommendations", [])
        print(f"  生成了 {len(recommendations)} 条建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"    {i}. {rec}")
    else:
        print(f"❌ 报告生成失败: {report_result.get('message')}")
        return
    
    print("\n=== 测试完成 ===")
    print("🎉 FinancialReportAgent功能测试全部通过！")


if __name__ == "__main__":
    asyncio.run(test_financial_analysis())