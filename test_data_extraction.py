#!/usr/bin/env python3

from src.agents.financial_report.tools import extract_financial_data, process_uploaded_financial_file

test_markdown = '''
| 项目 | 金额（万元） |
|------|-------------|
| 流动资产 | 10,000 |
| 非流动资产 | 20,000 |
| 总资产 | 30,000 |
| 营业收入 | 15,000 |
| 净利润 | 2,500 |
'''

# 处理文件
file_result = process_uploaded_financial_file.invoke({
    'file_content': test_markdown,
    'file_name': 'test.md',
    'file_type': 'md'
})

print('文件处理结果:')
print(f'表格数量: {file_result["table_count"]}')

# 提取数据
extract_result = extract_financial_data.invoke({
    'text_content': file_result['text_content'],
    'tables': file_result['tables'],
    'metrics': ['revenue', 'net_profit', 'total_assets']
})

print(f'提取结果状态: {extract_result["status"]}')
print(f'提取指标: {extract_result.get("extracted_metrics", {})}')

if extract_result['status'] == 'success':
    metrics = extract_result.get('extracted_metrics', {})
    for metric, value in metrics.items():
        if value is not None:
            print(f'  ✅ {metric}: {value:,} 万元')
        else:
            print(f'  ❌ {metric}: 未提取到')