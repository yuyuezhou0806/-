import pandas as pd

# 定义存储所有数据的列表
dfs = []

# 循环读取table1到table49的数据
for i in range(1, 50):
    sheet_name = f'Table {i}'
    # 读取指定工作表中的数据
    df = pd.read_excel('2244.xlsx', sheet_name=sheet_name)
    # 将数据添加到列表
    dfs.append(df)

# 使用concat函数合并所有数据
merged_df = pd.concat(dfs, ignore_index=True)

# 将合并后的数据保存到新的Excel文件
merged_df.to_excel('merged_table.xlsx', index=False)
