# Windows Task Scheduler Setup Guide

**Purpose**: Automate daily execution of Dunkin Sales Summary data pipelines  
**Date**: February 5, 2026

---

## 📋 Overview

This guide will help you set up Windows Task Scheduler to automatically run all three data pipelines daily:

1. **Sales Pipeline** (`run_dunkin_pipeline.bat`) - Dunkin sales data
2. **HME Pipeline** (`run_hme_pipeline.bat`) - Drive-thru performance metrics
3. **Medallia Pipeline** (`run_medallia_pipeline.bat`) - Guest reviews/comments

---

## 🕐 Recommended Schedule

**Time**: 9:00 AM daily (after morning emails arrive)

| Pipeline | Start Time | Duration | Purpose |
|----------|------------|----------|---------|
| Sales | 9:00 AM | ~2-3 min | Download & process sales data |
| HME | 9:05 AM | ~1-2 min | Download & upload drive-thru metrics |
| Medallia | 9:10 AM | ~1-2 min | Download & upload guest reviews |

**Why stagger?** Prevents conflicts with Gmail API rate limits and ensures one completes before the next starts.

---

## 🛠️ Step-by-Step Setup

### Task 1: Sales Pipeline

#### 1. Open Task Scheduler
- Press `Win + R`
- Type: `taskschd.msc`
- Press Enter

#### 2. Create New Task
- Click **"Create Task..."** (not "Create Basic Task")
- **Name**: `Dunkin Sales Pipeline - Daily`
- **Description**: `Downloads and processes daily sales data from Gmail`
- ✅ Check **"Run whether user is logged on or not"**
- ✅ Check **"Run with highest privileges"**
- **Configure for**: `Windows 10` (or your Windows version)

#### 3. Configure Triggers Tab
- Click **"New..."**
- **Begin the task**: `On a schedule`
- **Settings**: `Daily`
- **Start**: `9:00:00 AM`
- **Recur every**: `1 days`
- ✅ Check **"Enabled"**
- Click **OK**

#### 4. Configure Actions Tab
- Click **"New..."**
- **Action**: `Start a program`
- **Program/script**: `C:\Projects\Dunkin-sales-summary\run_dunkin_pipeline.bat`
- **Start in (optional)**: `C:\Projects\Dunkin-sales-summary`
- Click **OK**

#### 5. Configure Conditions Tab
- ⬜ **Uncheck** "Start the task only if the computer is on AC power"
- ✅ Check **"Wake the computer to run this task"** (optional)

#### 6. Configure Settings Tab
- ✅ Check **"Allow task to be run on demand"**
- ✅ Check **"Run task as soon as possible after a scheduled start is missed"**
- **If the task fails, restart every**: `5 minutes`
- **Attempt to restart up to**: `3 times`
- **Stop the task if it runs longer than**: `30 minutes`
- ✅ Check **"If the running task does not end when requested, force it to stop"**

#### 7. Save the Task
- Click **OK**
- Enter your Windows password when prompted
- Task is now created!

---

### Task 2: HME Pipeline

Repeat the same steps with these changes:

- **Name**: `Dunkin HME Pipeline - Daily`
- **Description**: `Downloads and processes HME drive-thru metrics from Gmail`
- **Start time**: `9:05:00 AM` (5 minutes after sales)
- **Program/script**: `C:\Projects\Dunkin-sales-summary\run_hme_pipeline.bat`

---

### Task 3: Medallia Pipeline

Repeat the same steps with these changes:

- **Name**: `Dunkin Medallia Pipeline - Daily`
- **Description**: `Downloads and processes guest comments from Gmail`
- **Start time**: `9:10:00 AM` (10 minutes after sales)
- **Program/script**: `C:\Projects\Dunkin-sales-summary\run_medallia_pipeline.bat`

---

## ✅ Testing Your Tasks

### Test Individual Task:
1. In Task Scheduler, find your task in the list
2. Right-click → **Run**
3. Check the **"Last Run Result"** column
   - `0x0` = Success ✅
   - Other codes = Error ❌

### Check Task History:
1. Select your task
2. Click **"History"** tab at bottom
3. Review execution events

### Verify Email Notifications:
- Check your email for success/failure notifications
- Each pipeline sends an email when it completes

### Check Log Files:
```
C:\Projects\Dunkin-sales-summary\logs\pipeline_20260205.log
C:\Projects\Dunkin-sales-summary\data\hme\logs\hme_pipeline_20260205.log
C:\Projects\Dunkin-sales-summary\logs\medallia_pipeline_20260205.log
```

---

## 🔧 Troubleshooting

### Task Shows "Running" But Never Completes
**Problem**: Script might be stuck waiting for user input (like `pause` command)

**Solution**: Remove or comment out `pause` from .bat files:
```batch
@echo off
cd /d "C:\Projects\Dunkin-sales-summary"
"C:\Users\dunki\AppData\Local\Programs\Python\Python313\python.exe" scripts\run_pipeline.py
REM pause  <- Comment this out for Task Scheduler
```

### Task Fails with Error Code
**Common Error Codes**:
- `0x1` - General error (check logs)
- `0x2` - File not found (check paths)
- `0x41303` - Task not ready to run

**Solution**:
1. Check the log file for specific error
2. Verify .bat file paths are correct
3. Ensure Python path is correct in .bat file
4. Run .bat file manually to test

### Task Doesn't Run at Scheduled Time
**Check**:
1. Computer must be on at scheduled time
2. If laptop, ensure "Wake computer to run task" is checked
3. Verify trigger is enabled
4. Check Windows Event Logs for scheduler errors

### Python Not Found Error
**Solution**: Update .bat files with full Python path:
```batch
"C:\Users\dunki\AppData\Local\Programs\Python\Python313\python.exe" scripts\run_pipeline.py
```

### Permission Denied Errors
**Solution**:
1. Edit task
2. Check "Run with highest privileges"
3. Save and re-enter password

---

## 📊 Monitoring Your Automated Tasks

### Daily Checks:
- ✅ Check email for success notifications (9:00-9:15 AM)
- ✅ If failure email received, check logs immediately

### Weekly Checks:
- Review Task Scheduler history
- Verify all three tasks ran successfully
- Check database for missing dates

### Monthly Checks:
- Review log files for patterns
- Verify data quality in dashboard
- Update .bat files if Python version changes

---

## 🎯 Quick Reference Commands

### View All Tasks in PowerShell:
```powershell
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Dunkin*"}
```

### Check Last Run Status:
```powershell
Get-ScheduledTask -TaskName "Dunkin Sales Pipeline - Daily" | Get-ScheduledTaskInfo
```

### Disable a Task Temporarily:
```powershell
Disable-ScheduledTask -TaskName "Dunkin Sales Pipeline - Daily"
```

### Enable a Task:
```powershell
Enable-ScheduledTask -TaskName "Dunkin Sales Pipeline - Daily"
```

### Run Task Manually:
```powershell
Start-ScheduledTask -TaskName "Dunkin Sales Pipeline - Daily"
```

---

## 📝 Alternative: Quick Setup Script

For advanced users, create this PowerShell script to set up all tasks at once:

**File**: `setup_scheduled_tasks.ps1`

```powershell
# Run as Administrator

# Task 1: Sales Pipeline
$action1 = New-ScheduledTaskAction -Execute "C:\Projects\Dunkin-sales-summary\run_dunkin_pipeline.bat" -WorkingDirectory "C:\Projects\Dunkin-sales-summary"
$trigger1 = New-ScheduledTaskTrigger -Daily -At 9:00AM
$settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "Dunkin Sales Pipeline - Daily" -Action $action1 -Trigger $trigger1 -Settings $settings1 -Description "Downloads and processes daily sales data from Gmail" -RunLevel Highest

# Task 2: HME Pipeline
$action2 = New-ScheduledTaskAction -Execute "C:\Projects\Dunkin-sales-summary\run_hme_pipeline.bat" -WorkingDirectory "C:\Projects\Dunkin-sales-summary"
$trigger2 = New-ScheduledTaskTrigger -Daily -At 9:05AM
$settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "Dunkin HME Pipeline - Daily" -Action $action2 -Trigger $trigger2 -Settings $settings2 -Description "Downloads and processes HME drive-thru metrics from Gmail" -RunLevel Highest

# Task 3: Medallia Pipeline
$action3 = New-ScheduledTaskAction -Execute "C:\Projects\Dunkin-sales-summary\run_medallia_pipeline.bat" -WorkingDirectory "C:\Projects\Dunkin-sales-summary"
$trigger3 = New-ScheduledTaskTrigger -Daily -At 9:10AM
$settings3 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "Dunkin Medallia Pipeline - Daily" -Action $action3 -Trigger $trigger3 -Settings $settings3 -Description "Downloads and processes guest comments from Gmail" -RunLevel Highest

Write-Host "All scheduled tasks created successfully!" -ForegroundColor Green
```

**To use**:
1. Right-click PowerShell → Run as Administrator
2. Run: `.\setup_scheduled_tasks.ps1`
3. All three tasks will be created automatically

---

## 🚨 Important Notes

### Computer Requirements:
- ✅ Computer must be ON at scheduled time (or use "Wake computer" option)
- ✅ Must have administrator privileges
- ✅ Python and all dependencies must be installed
- ✅ Gmail credentials in `.env` must be valid

### Best Practices:
- 🔐 Keep your Windows password updated in Task Scheduler
- 📧 Monitor email notifications daily
- 📝 Check logs weekly
- 🔄 Test tasks after Windows updates
- 💾 Keep backup of `.env` file

### Security:
- Tasks run with your user credentials
- Gmail app password stored in `.env` file
- Ensure `.env` is not shared or committed to git
- Use Windows Credential Manager for extra security

---

## 📅 Sample Weekly Schedule

| Day | Time | Action | Expected Result |
|-----|------|--------|-----------------|
| Mon-Fri | 9:00 AM | Sales pipeline runs | Email: ✅ Success |
| Mon-Fri | 9:05 AM | HME pipeline runs | Email: ✅ Success |
| Mon-Fri | 9:10 AM | Medallia pipeline runs | Email: ✅ Success |
| Sat-Sun | - | No runs scheduled | - |

*Note: Adjust schedule based on when your daily emails arrive*

---

## ✅ Success Checklist

After setup, verify:
- [ ] All 3 tasks created in Task Scheduler
- [ ] All 3 tasks show "Ready" status
- [ ] Triggers are enabled and show correct times
- [ ] Actions point to correct .bat files
- [ ] Settings configured correctly
- [ ] Manual test run successful (0x0 result)
- [ ] Email notifications working
- [ ] Log files being created
- [ ] Data appearing in database/dashboard

---

## 🆘 Getting Help

If tasks aren't working:
1. Check log files first
2. Run .bat files manually to test
3. Review Task Scheduler history
4. Check Windows Event Viewer for errors
5. Verify Gmail credentials are valid
6. Ensure Python path is correct

---

**Setup Complete!** 🎉

Your data pipelines will now run automatically every day, keeping your dashboard up-to-date with the latest sales, performance, and guest feedback data.

