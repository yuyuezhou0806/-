"""Check formula vs values of K, L, M, H for many cells in section 一."""
import win32com.client as w32

xl = w32.gencache.EnsureDispatch("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
wb = xl.Workbooks.Open(r"C:\Users\admin\Desktop\scan\three.xls", ReadOnly=True)
ws = wb.Sheets(1)

# Force recalc to be sure
xl.CalculateFullRebuild()

# Check rows 6-15 and 100, 150, 200, 213
print(f"{'Row':<4} {'F':<10} {'G':<10} {'H_form':<15} {'H_val':<10} {'I':<10} {'K_form':<12} {'K_val':<14} {'M_form':<12} {'M_val':<14}")
for r in [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 50, 100, 150, 200, 210, 213]:
    fv = ws.Cells(r, 6).Value
    gv = ws.Cells(r, 7).Value
    h_f = str(ws.Cells(r, 8).Formula)[:13]
    h_v = ws.Cells(r, 8).Value
    iv = ws.Cells(r, 9).Value
    k_f = str(ws.Cells(r, 11).Formula)[:10]
    k_v = ws.Cells(r, 11).Value
    m_f = str(ws.Cells(r, 13).Formula)[:10]
    m_v = ws.Cells(r, 13).Value
    print(f"{r:<4} {str(fv):<10} {str(gv):<10} {h_f:<15} {str(h_v):<10} {str(iv):<10} {k_f:<12} {str(k_v):<14} {m_f:<12} {str(m_v):<14}")

# Specifically: find rows where H formula is NOT =F+G and where K formula is NOT =F*I
print("\n--- Rows with non-formula H or K (checking 6-213) ---")
weird_h = []
weird_k = []
weird_m = []
for r in range(6, 214):
    h_f = str(ws.Cells(r, 8).Formula)
    k_f = str(ws.Cells(r, 11).Formula)
    m_f = str(ws.Cells(r, 13).Formula)
    if h_f and h_f != f'=F{r}+G{r}' and not h_f.startswith('='):
        weird_h.append((r, h_f))
    if k_f and k_f != f'=F{r}*I{r}' and not k_f.startswith('='):
        weird_k.append((r, k_f))
    if m_f and m_f != f'=H{r}*I{r}' and not m_f.startswith('='):
        weird_m.append((r, m_f))

print(f"Weird H (not formula): {len(weird_h)}")
for r, f in weird_h[:10]: print(f"  R{r}: H formula = {f!r}")
print(f"Weird K (not formula): {len(weird_k)}")
for r, f in weird_k[:10]: print(f"  R{r}: K formula = {f!r}")
print(f"Weird M (not formula): {len(weird_m)}")
for r, f in weird_m[:10]: print(f"  R{r}: M formula = {f!r}")

wb.Close(SaveChanges=False)
xl.Quit()
