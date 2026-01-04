# Australian Legal Intelligence Agent

Automated daily briefing system for monitoring Australian legal and regulatory developments.

## Data Sources

- **ASIC Insolvency Notices**: Companies entering external administration
- **ASIC Company Registers**: Director changes, company status updates
- **Federal Court**: Recent filings and judgments
- **ACCC**: Enforcement actions and media releases
- **ASX**: Market-sensitive announcements
- **AustLII**: Recent case law

## Setup Instructions

1. **Fork/Clone this repository**

2. **Add GitHub Secrets**:
   - Go to Settings → Secrets and variables → Actions
   - Add `ANTHROPIC_API_KEY` (required)
   - Add `SLACK_WEBHOOK` (optional, for Slack notifications)

3. **Configure Schedule**:
   - Edit `.github/workflows/daily-briefing.yml`
   - Adjust cron schedule for your timezone

4. **Test the Agent**:
   - Go to Actions tab
   - Click "Australian Legal Intelligence Briefing"
   - Click "Run workflow"

5. **Download Briefings**:
   - After each run, download from Actions → Artifacts

## Customization

Edit `agent.py` to:
- Add ASIC Connect API credentials
- Configure specific company monitoring
- Adjust data parsing for website changes
- Add email delivery

Edit `config.py` to set:
- Industry priorities
- Company size thresholds
- Conflict exclusions

## Cost

Approximately $0.05-0.15 per daily briefing using Claude API.

## Future Enhancements

- [ ] ASIC Connect API integration
- [ ] Email delivery via SendGrid/AWS SES
- [ ] Database storage for trend analysis
- [ ] Company-specific alerts
- [ ] Integration with CRM/practice management systems
