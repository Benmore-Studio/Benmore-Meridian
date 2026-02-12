# DigitalOcean Troubleshooting

> **Note:** This guide will be populated with common troubleshooting scenarios. For now, refer to the deployment and daily operations guides for issue-specific solutions.

## Quick Checklist

When something goes wrong:

1. **Check if app is running:**
   ```bash
   pm2 status | grep yourproject
   ```

2. **View recent logs:**
   ```bash
   pm2 logs yourproject --lines 50
   ```

3. **Check error logs only:**
   ```bash
   pm2 logs yourproject --err
   ```

4. **Use Claude for help:**
   ```bash
   claude
   ```
   Then describe your issue.

5. **Restart the app:**
   ```bash
   pm2 restart yourproject
   ```

6. **Verify deployment:**
   - Test URL in browser
   - Check for 500/404 errors
   - Review server logs

---

## Common Issues

### App Not Loading

**Symptoms:** Site returns 502 Bad Gateway or doesn't load

**Possible causes:**
- App crashed
- Port conflict
- Database connection failed
- Missing environment variables

**Fix:**
1. Check PM2 status: `pm2 status | grep yourproject`
2. View logs: `pm2 logs yourproject --err`
3. Restart: `pm2 restart yourproject`

### Database Errors

**Symptoms:** "no such table", "column does not exist", connection refused

**Possible causes:**
- Migrations not run
- Database doesn't exist
- Wrong credentials in `.env`

**Fix:**
1. Verify database exists: `sudo -u postgres psql -l`
2. Run migrations: `uv run python manage.py migrate`
3. Check `.env` database settings
4. Restart app: `pm2 restart yourproject`

### Static Files Not Loading

**Symptoms:** CSS/JS not working, plain HTML only

**Possible causes:**
- Static files not collected
- `STATIC_ROOT` not configured
- Nginx config issue

**Fix:**
```bash
cd /root/YOUR_REPOS/YOUR_PROJECT/BACKEND
uv run python manage.py collectstatic --noinput
pm2 restart yourproject
```

---

## Getting Help

1. **Check logs first** - Most errors show in logs
2. **Use Claude** - AI assistant on the server can help debug
3. **Review guides:**
   - [Getting Started](02-getting-started.md)
   - [Deployment](03-deployment.md)
   - [Daily Operations](04-daily-operations.md)
   - [Commands Reference](05-commands-reference.md)
4. **Ask team** - Post error message in team chat

---

**Back to:** [Overview](01-overview.md)
