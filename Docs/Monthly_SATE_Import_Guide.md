# ایمپورت ماهانهٔ داده‌های ساتع

راهنمای کامل و مرحله‌به‌مرحله در کنار گزارش‌های ایمپورت است:

`results\import_reports\Monthly_SATE_Import_StepByStep.md`

خلاصه: فایل‌های `Addin_Researchers/Demands/Proposals/Contracts.xlsx` را در `data\Add_In` بگذارید و اجرا کنید:

```
python scripts\addin_last_dates.py
python scripts\db_backup.py
python scripts\import_satec_addin.py --dry-run
python scripts\import_satec_addin.py
```
