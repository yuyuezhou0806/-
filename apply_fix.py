"""
Apply the fix: THREE.F = TWO.F + TWO.G (matched by serial number col A).
Use Excel COM so all formulas auto-recompute.
"""
import xlrd
import win32com.client as w32

TWO_PATH = r"C:\Users\admin\Desktop\scan\two.xls"
THREE_PATH = r"C:\Users\admin\Desktop\scan\three.xls"

# ---------- Step 1: Read TWO with xlrd ----------
def f(v):
    if v == '' or v is None: return 0.0
    if isinstance(v, str):
        try: return float(v.strip())
        except: return 0.0
    return float(v)

def is_data_row(row):
    a = row[0]
    if isinstance(a, float): return True
    if isinstance(a, str):
        try: float(a.strip()); return True
        except: return False
    return False

wb_two = xlrd.open_workbook(TWO_PATH)
sh_two = wb_two.sheet_by_index(0)

# section 一 in TWO ends just before "二、"
end_two = sh_two.nrows
for r in range(sh_two.nrows):
    a = str(sh_two.row_values(r)[0]).strip()
    if '二、' in a:
        end_two = r
        break

# Build serial -> (F+G) map from TWO
two_fg = {}  # serial -> F + G
two_meta = {}  # serial -> excel_row (for debug)
for r in range(5, end_two):
    raw = sh_two.row_values(r)
    if not is_data_row(raw): continue
    a_int = int(float(raw[0]))
    f_val = f(raw[5])
    g_val = f(raw[6])
    two_fg[a_int] = f_val + g_val
    two_meta[a_int] = r + 1

print(f"TWO: built F+G map for {len(two_fg)} serial numbers")

# ---------- Step 2: Open THREE via Excel COM and update F column ----------
xl = w32.gencache.EnsureDispatch("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
xl.ScreenUpdating = False

wb = xl.Workbooks.Open(THREE_PATH)
ws = wb.Sheets(1)

# find section 一 boundary in THREE
last_row = ws.UsedRange.Rows.Count
end_three = last_row
for r in range(1, last_row + 1):
    val = ws.Cells(r, 1).Value
    if val and '二、' in str(val):
        end_three = r  # 1-based; section 一 data ends before this
        break

print(f"THREE: section 一 spans rows 6 to {end_three - 1}")

# iterate rows 6 .. end_three - 1
updated = 0
unchanged = 0
no_serial = 0
no_match = 0
changes_log = []

for r in range(6, end_three):
    a_val = ws.Cells(r, 1).Value  # col A = serial number
    if a_val is None:
        no_serial += 1
        continue
    try:
        a_int = int(float(a_val))
    except (ValueError, TypeError):
        no_serial += 1
        continue

    if a_int not in two_fg:
        no_match += 1
        continue

    f_new = two_fg[a_int]
    f_old_raw = ws.Cells(r, 6).Value  # col F
    f_old = f(f_old_raw if f_old_raw is not None else '')

    if abs(f_new - f_old) < 0.0001:
        unchanged += 1
        continue

    ws.Cells(r, 6).Value = f_new
    updated += 1
    changes_log.append((r, a_int, f_old, f_new))

print(f"\n--- F column update results ---")
print(f"  Updated:    {updated}")
print(f"  Unchanged:  {unchanged}")
print(f"  No serial:  {no_serial}")
print(f"  No match in TWO: {no_match}")

# ---------- Step 3: Force full recalculation ----------
xl.CalculateFullRebuild()
print("\n--- Full Excel recalc done ---")

# ---------- Step 4: Read updated totals ----------
print("\n--- Post-update totals ---")
for cell in ['K5', 'L5', 'M5', 'K217', 'L217', 'M217', 'K219', 'L219', 'M219', 'L229', 'M229']:
    val = ws.Range(cell).Value
    print(f"  {cell} = {val}")

# Specifically check M229 (grand total M)
m229 = ws.Range("M229").Value
expected = 14142643.7
delta = m229 - expected
print(f"\n=== M229 (合计 M, 累计本月产值) = {m229:,.4f} ===")
print(f"Expected: {expected:,.4f}")
print(f"Delta:    {delta:+,.4f}")

# ---------- Step 5: Save and close ----------
wb.Save()
wb.Close(SaveChanges=False)
xl.Quit()

print("\nSaved THREE.xls. Done.")
