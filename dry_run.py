"""Dry run v3: match by serial number (col A)."""
import xlrd

TWO_PATH = r"C:\Users\admin\Desktop\scan\two.xls"
THREE_PATH = r"C:\Users\admin\Desktop\scan\three.xls"

COL_A_NUM = 0; COL_B_CAT = 1; COL_C_NAME = 2; COL_D_UNIT = 3
COL_E_CONTRACT = 4; COL_F_LASTMONTH = 5; COL_G_THISMONTH = 6
COL_H_CUMUL = 7; COL_I_PRICE = 8
COL_K_PASTPROD = 10; COL_L_THISMOPROD = 11; COL_M_CUMULPROD = 12

def f(v):
    if v == '' or v is None: return 0.0
    if isinstance(v, str):
        try: return float(v.strip())
        except: return 0.0
    return float(v)

def is_data_row(row):
    a = row[COL_A_NUM]
    if isinstance(a, float): return True
    if isinstance(a, str):
        try: float(a.strip()); return True
        except: return False
    return False

def parse(path, label):
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    end = sh.nrows
    for r in range(sh.nrows):
        a = str(sh.row_values(r)[COL_A_NUM]).strip()
        if '二、' in a:
            end = r
            break
    rows = {}
    last_b = ''
    for r in range(5, end):
        raw = sh.row_values(r)
        if not is_data_row(raw): continue
        a_int = int(float(raw[COL_A_NUM]))
        b_raw = str(raw[COL_B_CAT]).strip()
        if b_raw: last_b = b_raw
        b = b_raw if b_raw else last_b
        rows[a_int] = {
            'rownum': r + 1, 'a': a_int, 'b': b,
            'c': str(raw[COL_C_NAME]).strip(),
            'd': str(raw[COL_D_UNIT]).strip(),
            'f': f(raw[COL_F_LASTMONTH]),
            'g': f(raw[COL_G_THISMONTH]),
            'h': f(raw[COL_H_CUMUL]),
            'i': f(raw[COL_I_PRICE]),
            'k': f(raw[COL_K_PASTPROD]),
            'l': f(raw[COL_L_THISMOPROD]),
            'm': f(raw[COL_M_CUMULPROD]),
        }
    print(f'{label}: serial range {min(rows)}-{max(rows)}, unique={len(rows)}')
    return rows

two_map = parse(TWO_PATH, 'TWO')
three_map = parse(THREE_PATH, 'THREE')

# Predict
matched = 0
unmatched_serial = []
content_mismatch = []
old_K = 0; old_L = 0; old_M = 0
new_K = 0; new_M = 0
unchanged = 0

for a, r in three_map.items():
    old_K += r['k']; old_L += r['l']; old_M += r['m']
    if a in two_map:
        matched += 1
        t = two_map[a]
        # Sanity check content match
        if t['c'] != r['c'] or t['d'] != r['d']:
            content_mismatch.append((a, r, t))
        f_new = t['f'] + t['g']
        if abs(f_new - r['f']) < 0.001:
            unchanged += 1
    else:
        unmatched_serial.append(a)
        f_new = r['f']
    h_new = f_new + r['g']
    k_new = f_new * r['i']
    m_new = h_new * r['i']
    new_K += k_new
    new_M += m_new

print(f'\nMatching by serial:')
print(f'  Matched: {matched}, unmatched: {len(unmatched_serial)} {unmatched_serial}')
print(f'  Of matched: F unchanged={unchanged}, F changed={matched-unchanged}')
print(f'  Content mismatches (same serial, different C/D): {len(content_mismatch)}')
for a, th, t in content_mismatch[:5]:
    print(f'    Serial {a}: TWO=({t["b"][:6]}, "{t["c"][:25]}", {t["d"]}) F+G={t["f"]+t["g"]} | THREE=({th["b"][:6]}, "{th["c"][:25]}", {th["d"]}) currentF={th["f"]}')

print(f'\nSection 一 totals:')
print(f'  Old K: {old_K:>16,.4f}     Old L: {old_L:>16,.4f}     Old M: {old_M:>16,.4f}')
print(f'  New K: {new_K:>16,.4f}                                  New M: {new_M:>16,.4f}')
print(f'  ΔK = {new_K - old_K:+,.4f}')

# Section 三 (税金)
new_section3_M = (new_K + old_L) * 0.06

# Section 四 (扣款) - read from current
wb = xlrd.open_workbook(THREE_PATH)
sh = wb.sheet_by_index(0)
section_4_M = f(sh.row_values(218)[COL_M_CUMULPROD])

new_grand_M = new_M + 0 + new_section3_M - section_4_M
print(f'\nGrand total M (五):')
print(f'  = M_一({new_M:,.2f}) + 0 + M_三({new_section3_M:,.2f}) - M_四({section_4_M:,.2f})')
print(f'  = {new_grand_M:,.4f}')
print(f'  Expected: 14,142,643.7')
print(f'  Delta:    {new_grand_M - 14142643.7:+,.4f}')
