# Dashboard Changelog

## Version 1.1 - Excel Export Feature

### Added
- **Excel Download Button**: Users can now export the annual financial breakdown table to Excel
- **`to_excel()` helper function**: Converts DataFrame to Excel format using BytesIO buffer
- **Dynamic filename**: Export files are named `financial_report_{employer_code}.xlsx` for easy identification

### Technical Details
- Import added: `io` from standard library
- Function signature: `to_excel(df) -> bytes`
- Uses `openpyxl` engine (already in requirements.txt)
- Button placed directly below the annual breakdown table
- Proper MIME type set for Excel downloads: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### User Experience
- Button label in Persian: "📥 دانلود گزارش به صورت اکسل"
- One-click download with no additional configuration needed
- Downloaded file preserves Persian column names and all formatting
- Numbers are exported in their numeric format (not comma-formatted strings) for further Excel calculations

### Code Changes
**File**: `dashboard/app.py`
- Line 3: Added `import io`
- Lines 140-144: New `to_excel()` helper function
- Lines 289-294: New `st.download_button` component

### Dependencies
No new dependencies required - `openpyxl` was already in requirements.txt

---

## Version 1.0 - Initial Release

### Features
- Employer selection dropdown
- Hierarchical support (Mother + Subsidiaries)
- Six KPI metrics
- Annual breakdown table
- Trend analysis chart
- Persian UI with RTL support
