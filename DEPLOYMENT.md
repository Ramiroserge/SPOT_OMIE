# 🚀 Deployment Guide - GitHub Actions Scheduled Sync

This guide will help you set up automated hourly syncs for the SPOT-to-OMIE application using GitHub Actions.

## 📋 Prerequisites

1. A GitHub repository for this project
2. Your API credentials:
   - `SPOT_ACCESS_KEY`
   - `OMIE_APP_KEY`
   - `OMIE_APP_SECRET`

## 🛠️ Setup Steps

### 1. Set Up GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**, and add these secrets:

1. **`SPOT_ACCESS_KEY`**
   - Your SPOT API access key

2. **`OMIE_APP_KEY`**
   - Your OMIE application key

3. **`OMIE_APP_SECRET`**
   - Your OMIE application secret

### 2. Push to GitHub

```bash
git add .
git commit -m "Add GitHub Actions scheduled sync workflow"
git push origin main
```

That's it! The workflow will now run automatically every hour.

## ⏰ Scheduled Runs

The GitHub Actions workflow (`.github/workflows/scheduled-sync.yml`) is configured to run automatically every hour.

### Schedule Details
- **Cron Expression:** `0 * * * *` (every hour at minute 0)
- **Timezone:** UTC (GitHub Actions default)
- **Python Version:** 3.11

### Manual Trigger

You can also trigger the sync manually:
1. Go to your GitHub repository
2. Click on **Actions** tab
3. Select **Scheduled SPOT to OMIE Sync**
4. Click **Run workflow** → **Run workflow**

## 🔍 Monitoring

### Check GitHub Actions Logs
1. Go to your repository's **Actions** tab
2. Click on any workflow run to see detailed logs
3. Expand the "Run SPOT to OMIE Sync" step to see sync output

## 💰 Cost

This setup is **completely free**:
- GitHub Actions provides 2,000 free minutes/month for private repos
- Unlimited for public repos
- Your sync takes ~1-2 minutes, so even at hourly runs (24 × 30 = 720 minutes/month), you're well within limits

## 🛑 Troubleshooting

### Workflow Not Running
- Check that your repository has Actions enabled in Settings
- Verify the cron schedule in `.github/workflows/scheduled-sync.yml`
- Note: GitHub Actions may delay scheduled workflows by 3-10 minutes during high load

### Sync Fails
- Check that all secrets (API keys) are set correctly in GitHub Settings → Secrets
- Review the workflow logs in the Actions tab
- Test your credentials locally by running `python app/main.py` with a `.env` file

### Permission Issues
- Ensure your GitHub Actions has write permissions (Settings → Actions → General → Workflow permissions)

## 📝 Notes

- The workflow runs on GitHub's `ubuntu-latest` runners
- Dependencies are cached for faster execution
- You can change the schedule by modifying the cron expression in the workflow file
- The workflow also runs on `workflow_dispatch` so you can trigger it manually anytime

## 🔧 Customizing the Schedule

Edit `.github/workflows/scheduled-sync.yml` and change the cron expression:

```yaml
schedule:
  - cron: '0 * * * *'  # Every hour
  # - cron: '0 */2 * * *'  # Every 2 hours
  # - cron: '0 9 * * *'  # Daily at 9 AM UTC
  # - cron: '0 9 * * 1-5'  # Weekdays at 9 AM UTC
```

