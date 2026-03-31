# -*- coding: utf-8 -*-
"""
数据结构探索脚本
"""
import pandas as pd
import os
import sys

# 修复Windows控制台编码问题
sys.stdout.reconfigure(encoding='utf-8')

pd.set_option('display.max_columns', 150)
pd.set_option('display.width', 300)

def explore_file(file_path, name):
    """探索单个数据文件"""
    print(f"\n{'='*80}")
    print(f" {name}")
    print(f" 文件: {file_path}")
    print("="*80)

    try:
        # 读取数据
        with pd.read_stata(file_path, chunksize=100) as reader:
            for df in reader:
                break

        print(f"\n总列数: {len(df.columns)}")
        print(f"样本行数: {len(df)}")

        # 字段详情
        print(f"\n字段详情:")
        print("-"*80)
        for i, col in enumerate(df.columns, 1):
            dtype = str(df[col].dtype)
            sample = df[col].dropna().head(1).tolist()
            sample_str = str(sample[0])[:40] if sample else "(空)"
            print(f"{i:3d}. {col:<35} [{dtype:<10}] {sample_str}")

        # 查找关键字段
        print(f"\n关键字段检测:")

        keywords = {
            '邮编': ['yzbm', 'zipcode', '邮政编码', 'yb', 'post_code', 'youbian', 'post', 'zip'],
            '电话': ['dhhm', 'phone', '电话号码', 'tel', 'telephone', 'lxdh'],
            '组织机构代码': ['org_code', 'org_code_new', '组织机构代码', 'orgcode', 'zzjgdm'],
            '企业名称': ['qymc', 'enterprise_name', '企业名称', 'firm_name', 'company_name', 'company', 'dwmc'],
            '海关编码': ['customs_code', 'hg_code', '海关注册编码', 'enterprise_id', 'qybm'],
        }

        df_cols_lower = {str(col).lower().strip(): col for col in df.columns}

        for key_name, candidates in keywords.items():
            found = None
            for c in candidates:
                if c.lower() in df_cols_lower:
                    found = df_cols_lower[c.lower()]
                    break
                if c in df.columns:
                    found = c
                    break
            if found:
                samples = df[found].dropna().head(3).tolist()
                print(f"  [OK] {key_name}: {found}")
                print(f"        示例: {samples}")
            else:
                print(f"  [--] {key_name}: 未找到")

        # 显示前几行数据
        print(f"\n数据预览 (前3行):")
        print(df.head(3))

        return df.columns.tolist()

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    print("\n" + "#"*80)
    print("# 数据结构探索工具")
    print("#"*80)

    # 探索工业企业数据
    firm_file = "工业企业数据/merge_2000.dta"
    if os.path.exists(firm_file):
        firm_cols = explore_file(firm_file, "工业企业数据 (2000年)")
    else:
        firm_cols = []

    # 探索海关数据
    customs_file = "海关原始数据/2000.dta"
    if os.path.exists(customs_file):
        customs_cols = explore_file(customs_file, "海关数据 (2000年)")
    else:
        customs_cols = []

    print("\n" + "#"*80)
    print("# 探索完成")
    print("#"*80)


if __name__ == "__main__":
    main()
