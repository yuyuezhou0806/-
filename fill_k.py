"""Fill missing K formulas (=F*I) in section 一 rows where K is empty."""
import win32com.client as w32

xl = w32.gencache.EnsureDispatch("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
xl.ScreenUpdating = False

wb = xl.Workbooks.Open(r"C:\Users\admin\Desktop\scan\three.xls")
ws = wb.Sheets(1)

filled = 0
for r in range(6, 214):
    k_formula = ws.Cells(r, 11).Formula  # col K
    if not k_formula or k_formula == '':
        # Empty K cell — fill with =F{r}*I{r}
        ws.Cells(r, 11).Formula = f"=F{r}*I{r}"
        filled += 1

print(f"Filled K formulas in {filled} rows")

xl.CalculateFullRebuild()

m229 = ws.Range("M229").Value
print(f"\nM229 = {m229:,.4f}")
print(f"Expected: 14,142,643.70")
print(f"Delta: {m229 - 14142643.7:+,.4f}")

# Final totals
print(f"\nFinal section 一 totals:")
for c in ['K5', 'L5', 'M5', 'M217', 'M219', 'M229']:
    v = ws.Range(c).Value
    print(f"  {c} = {v:,.4f}" if isinstance(v, (int, float)) else f"  {c} = {v}")

wb.Save()
wb.Close(SaveChanges=False)
xl.Quit()
print("\nSaved.")
