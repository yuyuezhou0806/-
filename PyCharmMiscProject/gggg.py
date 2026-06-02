import pandas as pd

# 读取Excel文件
file_path = r"C:\Users\admin\Desktop\水利（1.1-10.31）.xls"  # 请确保文件路径正确
df = pd.read_excel(file_path)


# 按B列（试验编号）分组，合并G列（施工部位）的数据
def merge_construction_sites(sites):
    """
    合并施工部位数据的自定义函数
    过滤空值并用分号连接
    """
    # 过滤掉空值和NaN值，确保只处理有效数据
    valid_sites = [str(site) for site in sites if pd.notna(site) and str(site).strip() != '']

    if len(valid_sites) == 0:
        return ''  # 如果没有有效数据，返回空字符串
    elif len(valid_sites) == 1:
        return valid_sites[0]  # 如果只有一个有效数据，直接返回
    else:
        return '；'.join(valid_sites)  # 多个数据用分号连接


# 按B列分组并聚合数据
grouped_df = df.groupby('试验编号').agg({
    '委托单号': 'first',  # 保留第一个委托单号
    '工程名称': 'first',  # 保留第一个工程名称
    '委托日期': 'first',  # 保留第一个委托日期
    '样品名称': 'first',  # 保留第一个样品名称
    '样品规格': 'first',  # 保留第一个样品规格
    '项目名称': 'first',  # 保留第一个项目名称
    '施工部位': merge_construction_sites,  # 合并G列数据
    '试验结果': 'first'  # 保留第一个试验结果
}).reset_index()

# 重新排列列顺序，保持与原表一致
column_order = ['委托单号', '试验编号', '工程名称', '委托日期', '样品名称',
                '样品规格', '项目名称', '施工部位', '试验结果']
grouped_df = grouped_df[column_order]

# 显示处理效果对比
print("数据处理完成！")
print(f"原始数据行数: {len(df)}")
print(f"处理后数据行数: {len(grouped_df)}")
print(f"合并减少了 {len(df) - len(grouped_df)} 行重复数据")

# 保存结果到新文件
output_path = "水利数据_已合并G列.xlsx"
grouped_df.to_excel(output_path, index=False)
print(f"处理后的数据已保存至: {output_path}")

# 显示几个合并示例
print("\nG列合并效果示例:")
sample_data = grouped_df[grouped_df['施工部位'].str.contains('；')].head(3)
for idx, row in sample_data.iterrows():
    print(f"试验编号: {row['试验编号']}")
    print(f"合并后的施工部位: {row['施工部位']}")
    print("---")