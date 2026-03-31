# -*- coding: utf-8 -*-
"""检查新工业企业数据字段"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("检查工业企业数据库-新 字段结构")
print("="*80)

# 检查2001年和2005年数据
for year in [2001, 2005]:
    file_path = f"工业企业数据库-新/工业企业数据{year}.dta"
    try:
        with pd.read_stata(file_path, chunksize=50) as reader:
            df = next(reader)

        print(f"\n{year}年数据 - 共{len(df.columns)}个字段")

        # 查找关键字段
        keywords = ['名称', '邮编', '电话', '地址', '代码', '标识', '编码', '法人', '联系',
                    'name', 'code', 'tel', 'zip', 'addr', 'org']

        print(f"\n包含关键词的字段:")
        for col in df.columns:
            col_lower = str(col).lower()
            for kw in keywords:
                if kw.lower() in col_lower:
                    sample = df[col].dropna().head(2).tolist()
                    print(f"  - {col}: {sample}")
                    break

        # 显示所有字段
        print(f"\n所有字段列表:")
        for i, col in enumerate(df.columns, 1):
            sample = df[col].dropna().head(1).tolist()
            sample_str = str(sample[0])[:40] if sample else "(空)"
            print(f"  {i:3d}. {col:<35} {sample_str}")

    except Exception as e:
        print(f"  读取失败: {e}")

print("\n" + "="*80)
