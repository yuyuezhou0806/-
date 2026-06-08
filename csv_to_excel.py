import pandas as pd
from pathlib import Path
from datetime import datetime
# 1.读取文件夹内所有 CSV
folder = input("CSV 文件夹路径: ").strip().strip('\'"')
folder_path = Path(folder)
csv_files = list(folder_path.glob("*.csv"))
print(f"找到 {len(csv_files)} 个 CSV 文件")
all_data = []
fail_list = []
for f in csv_files:
    try:
        df = pd.read_csv(f, encoding="utf-8")
    except:
        try:
            df = pd.read_csv(f, encoding="gbk")
        except:
            print(f"  [跳过] {f.name} - 无法读取")
            fail_list.append(f.name)
            continue
    if len(df) == 0:
        print(f"  [跳过] {f.name} - 空文件")
        continue
    df["来源文件"] = f.name
    all_data.append(df)
    print(f"  [OK] {f.name} ({len(df)} 行)")
# 2.合并
df = pd.concat(all_data, ignore_index=True)
print(f"\n合并后: {len(df)} 行 × {len(df.columns)} 列")
# 3.pandas 清洗 + 去重
df.columns = df.columns.str.strip()
for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].str.strip()
df.dropna(how="all", inplace=True)
before = len(df)
df.drop_duplicates(inplace=True)
print(f"去重: {before} → {len(df)} (删除了 {before - len(df)} 行)")
# 4.保存为 Excel
output = input("输出文件名 (回车默认 output): ").strip() or "output"
filename = f"{output}.xlsx"
with pd.ExcelWriter(filename, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="数据", index=False)
    # 概况
    summary = pd.DataFrame({
        "项目": ["总行数", "总列数", "处理文件数", "失败文件数"],
        "数值": [len(df), len(df.columns), len(csv_files), len(fail_list)]
    })
    summary.to_excel(writer, sheet_name="概况", index=False)
    if fail_list:
        pd.DataFrame({"失败文件": fail_list}).to_excel(writer, sheet_name="失败清单", index=False)
# 5.保存日志
log_name = f"{output}_日志.txt"
with open(log_name, "w", encoding="utf-8") as f:
    f.write(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"文件夹: {folder}\n")
    f.write(f"处理文件数: {len(csv_files)}\n")
    f.write(f"失败文件数: {len(fail_list)}\n")
    f.write(f"最终行数: {len(df)}\n")
    f.write(f"最终列数: {len(df.columns)}\n")
    if fail_list:
        f.write(f"失败文件:\n")
        for fn in fail_list:
            f.write(f"  - {fn}\n")
print(f"\n完成: {filename}")
print(f"日志: {log_name}")
