"""Read both .xls files and print structure to understand the data."""
import xlrd

def inspect(path, label):
    print(f"\n========== {label}: {path} ==========")
    wb = xlrd.open_workbook(path, formatting_info=False)
    print("Sheets:", wb.sheet_names())
    for sn in wb.sheet_names():
        sh = wb.sheet_by_name(sn)
        print(f"\n--- Sheet: {sn} (rows={sh.nrows}, cols={sh.ncols}) ---")
        # print first 10 rows
        for r in range(min(sh.nrows, 12)):
            row = []
            for c in range(sh.ncols):
                v = sh.cell_value(r, c)
                if isinstance(v, float):
                    v = round(v, 4)
                row.append(str(v)[:25])
            print(f"  R{r+1:3}: {row}")
        if sh.nrows > 12:
            print(f"  ... ({sh.nrows} rows total)")

inspect(r"C:\Users\admin\Desktop\scan\two.xls", "TWO")
inspect(r"C:\Users\admin\Desktop\scan\three.xls", "THREE")
