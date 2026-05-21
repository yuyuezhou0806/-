"""Diagnostic: see per-row contributions and look for largest deltas."""
import xlrd

TWO_PATH = r"C:\Users\admin\Desktop\scan\two.xls"
THREE_PATH = r"C:\Users\admin\Desktop\scan\three.xls"

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

# Read TWO
wb_two = xlrd.open_workbook(TWO_PATH)
sh_two = wb_two.sheet_by_index(0)
two = {}
for r in range(5, 222):
    raw = sh_two.row_values(r)
    if not is_data_row(raw): continue
    a = int(float(raw[0]))
    two[a] = {
        'rownum': r+1, 'b': str(raw[1]).strip(), 'c': str(raw[2]).strip(),
        'd': str(raw[3]).strip(), 'f': f(raw[5]), 'g': f(raw[6]),
        'i': f(raw[8]), 'h': f(raw[7])
    }

# Read THREE (post-update)
wb_three = xlrd.open_workbook(THREE_PATH)
sh_three = wb_three.sheet_by_index(0)
three = {}
for r in range(5, 213):
    raw = sh_three.row_values(r)
    if not is_data_row(raw): continue
    a = int(float(raw[0]))
    three[a] = {
        'rownum': r+1, 'b': str(raw[1]).strip(), 'c': str(raw[2]).strip(),
        'd': str(raw[3]).strip(),
        'f': f(raw[5]), 'g': f(raw[6]), 'h': f(raw[7]),
        'i': f(raw[8]), 'k': f(raw[10]), 'l': f(raw[11]), 'm': f(raw[12]),
    }

# Compare TWO.F+TWO.G to THREE.F (should be equal after fix)
print("=== Rows where THREE.F != TWO.F+TWO.G (after the fix) ===")
mismatches = []
for a, t in two.items():
    if a not in three: continue
    expected_f = t['f'] + t['g']
    actual_f = three[a]['f']
    if abs(expected_f - actual_f) > 0.001:
        mismatches.append((a, expected_f, actual_f, t['c'], t['i']))

print(f"Total mismatches: {len(mismatches)}")
for m in mismatches[:30]:
    a, exp, act, c, i = m
    delta_k = (exp - act) * i
    print(f"  Serial {a:>3} | THREE.F={act:>10.2f} should be {exp:>10.2f} | diff = {exp-act:>10.2f} → ΔK if fixed = {delta_k:>14,.2f} | {c[:30]}")

# Also: check 单价 (I) differences between TWO and THREE
print("\n=== I (单价) differences between TWO and THREE ===")
i_diffs = []
for a in three:
    if a not in two: continue
    if abs(three[a]['i'] - two[a]['i']) > 0.001:
        i_diffs.append(a)
print(f"Rows where I differs: {len(i_diffs)}")
for a in i_diffs[:10]:
    print(f"  Serial {a}: TWO.I={two[a]['i']:.4f}, THREE.I={three[a]['i']:.4f}")

# Compute total ΔK if we fix all mismatches
total_delta_k = sum((exp - act) * i for a, exp, act, c, i in mismatches)
print(f"\n=== Total ΔK if all mismatches fixed: {total_delta_k:,.4f} ===")

# Check THREE row 6's F before and after — verify F was updated
print(f"\nSample rows after fix (THREE side):")
for sn in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 130, 215]:
    if sn in three:
        t = three[sn]
        if sn in two:
            tt = two[sn]
            print(f"  Serial {sn}: THREE.F={t['f']:>9.2f}, TWO.F+G={tt['f']+tt['g']:>9.2f}, K={t['k']:>14,.2f}, M={t['m']:>14,.2f}")
        else:
            print(f"  Serial {sn}: THREE.F={t['f']:>9.2f}, [no TWO match]")
