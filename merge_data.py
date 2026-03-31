# -*- coding: utf-8 -*-
"""
工业企业数据与海关数据合并程序
"""
import pandas as pd
import os
import sys
import gc

sys.stdout.reconfigure(encoding='utf-8')

FIRM_DATA_FOLDER = "工业企业数据库-新"
CUSTOMS_DATA_FOLDER = "海关原始数据"
OUTPUT_FOLDER = "合并结果"
YEAR = 2000  # 可修改年份

FIRM_COLS = [
    '企业名称', '邮政编码', '固定电话',
    '资产总计千元', '登记注册类型', '出口交货值千元'
]

def format_zip(x):
    if pd.isna(x):
        return None
    s = str(int(x) if isinstance(x, float) else x).strip()
    return s.zfill(6)[:6] if len(s) >= 4 else None

def format_tel(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    s = s.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    return s[-7:] if len(s) >= 7 else None

def standardize_name(x):
    if pd.isna(x):
        return None
    name = str(x).strip()
    for suffix in ['有限公司', '有限责任公司', '股份有限公司', '集团', '公司', '厂']:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    return name.replace(' ', '').replace('　', '').strip()

def find_company_field(cols):
    """查找企业名称字段，优先顺序：company > firm_name > entnm > 企业名称"""
    priority = ['company', 'firm_name', 'entnm', '企业名称']
    for p in priority:
        if p in cols:
            return p
    # 如果没有精确匹配，查找包含关键词的字段
    for col in cols:
        col_lower = col.lower()
        if 'company' == col_lower or col_lower == 'company':
            return col
        if 'entnm' in col_lower or '企业名称' in col:
            return col
    return None

def main():
    print("=" * 50)
    print(f"合并 {YEAR} 年数据")
    print("=" * 50)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # 读取工业企业数据
    print("\n读取工业企业数据...")
    firm_file = f"{FIRM_DATA_FOLDER}/工业企业数据{YEAR}.dta"

    firm_dfs = []
    with pd.read_stata(firm_file, chunksize=50000) as reader:
        for i, chunk in enumerate(reader):
            chunk = chunk[[c for c in FIRM_COLS if c in chunk.columns]]
            firm_dfs.append(chunk)
            print(f"  块{i+1}: {len(chunk):,}条")

    firm_df = pd.concat(firm_dfs, ignore_index=True)
    del firm_dfs
    gc.collect()
    print(f"工业企业: {len(firm_df):,} 条")

    # 读取海关数据
    print("\n检查海关数据...")
    customs_file = f"{CUSTOMS_DATA_FOLDER}/{YEAR}.dta"

    with pd.read_stata(customs_file, chunksize=1) as reader:
        df_check = next(reader)
        customs_cols = df_check.columns.tolist()

    print(f"海关数据列名: {customs_cols}")

    name_field = find_company_field(customs_cols)
    print(f"找到企业名称字段: {name_field}")

    customs_read_cols = [name_field, 'value'] if name_field else ['value']

    customs_dfs = []
    with pd.read_stata(customs_file, chunksize=200000) as reader:
        for i, chunk in enumerate(reader):
            chunk = chunk[[c for c in customs_read_cols if c in chunk.columns]]
            customs_dfs.append(chunk)
            print(f"  块{i+1}: {len(chunk):,}条")

    customs_df = pd.concat(customs_dfs, ignore_index=True)
    del customs_dfs
    gc.collect()
    print(f"海关: {len(customs_df):,} 条")

    if not name_field:
        print("没有可用的匹配字段！")
        return

    # 匹配
    print(f"\n使用 {name_field} 匹配...")

    firm_df['_key'] = firm_df['企业名称'].apply(standardize_name)
    customs_df['_key'] = customs_df[name_field].apply(standardize_name)

    firm_valid = firm_df[firm_df['_key'].notna() & (firm_df['_key'] != '')]
    customs_valid = customs_df[customs_df['_key'].notna() & (customs_df['_key'] != '')]

    print(f"工业企业有效键: {len(firm_valid):,}")
    print(f"海关有效键: {len(customs_valid):,}")

    firm_unique = firm_valid.drop_duplicates(subset=['_key'], keep='first')
    customs_unique = customs_valid.drop_duplicates(subset=['_key'], keep='first')

    del firm_valid, customs_valid
    gc.collect()

    print(f"工业企业去重: {len(firm_unique):,}")
    print(f"海关去重: {len(customs_unique):,}")

    merged = pd.merge(
        firm_unique, customs_unique,
        on='_key', how='inner',
        suffixes=('_firm', '_customs')
    )

    del firm_unique, customs_unique, firm_df, customs_df
    gc.collect()

    merged.drop(['_key'], axis=1, inplace=True, errors='ignore')
    merged['year'] = YEAR

    merged = merged.rename(columns={
        '企业名称': 'firm_name',
        '邮政编码': 'zipcode',
        '固定电话': 'phone',
        '资产总计千元': 'total_assets',
        '登记注册类型': 'firm_type',
        '出口交货值千元': 'export_value',
        name_field: 'company',
        'value': 'trade_value'
    })

    print(f"\n合并结果: {len(merged):,} 条")

    if len(merged) > 0:
        output_file = f"{OUTPUT_FOLDER}/merged_{YEAR}.csv"
        merged.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"已保存: {output_file}")
        print(f"\n字段: {merged.columns.tolist()}")
        print(merged.head(3))

    del merged
    gc.collect()
    print("\n内存已清理")

if __name__ == "__main__":
    main()