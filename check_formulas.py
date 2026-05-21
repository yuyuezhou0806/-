"""Quick check: do K, M cells have formulas or hardcoded values in three.xls?"""
import win32com.client as w32

xl = w32.gencache.EnsureDispatch("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
wb = xl.Workbooks.Open(r"C:\Users\admin\Desktop\scan\three.xls", ReadOnly=True)
ws = wb.Sheets(1)

# Check formula vs value for several cells
print("=== Cell Formula vs Value (THREE.xls) ===")
print(f"{'Cell':<8} {'Formula':<40} {'Value':<20}")
for cell in ["F6", "F7", "K6", "L6", "M6", "K7", "M7", "F215", "K215", "M215", "K218", "M218", "K220", "M220", "K229", "L229", "M229"]:
    try:
        formula = ws.Range(cell).Formula
        value = ws.Range(cell).Value
        print(f"{cell:<8} {str(formula)[:38]:<40} {str(value):<20}")
    except Exception as e:
        print(f"{cell:<8} ERROR: {e}")

# Also row 5 (totals for section 一)
print("\n=== Row 5 (section 一 totals) ===")
for col in ['J', 'K', 'L', 'M']:
    cell = f"{col}5"
    formula = ws.Range(cell).Formula
    value = ws.Range(cell).Value
    print(f"{cell}: formula={str(formula)[:60]} value={value}")

wb.Close(SaveChanges=False)
xl.Quit()
print("Done")
