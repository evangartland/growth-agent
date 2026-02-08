# CLAUDE.md - AI Assistant Guide for growth-agent

## Project Overview

Australian Employment Law Intelligence Agent. Generates daily briefings on employment law matters, adverse action triggers, and advisory opportunities for a legal firm's business development.

**Domain**: Australian employment law (adverse action, whistleblowing, restructures, modern awards)
**Target Industries**: Retail, Construction, Healthcare, Manufacturing, Financial Services
**Stack**: Python 3.11, Anthropic Claude API, BeautifulSoup, Requests, SMTP

## Repository Structure

```
growth-agent/
├── agent.py              # Main agent (single-file, ~1,680 lines) - all core logic
├── config.py             # Placeholder credentials (cookies, API keys)
├── requirements.txt      # Python dependencies (no pinned versions)
├── README.md             # Landing page documentation
├── .gitignore            # Standard Python ignores + briefing outputs
└── .github/workflows/
    ├── daily-briefing.yml  # Production workflow (6 AM AEST Mon-Fri)
    └── blank.yml           # Deprecated template
```

## Architecture

### Single-file design (`agent.py`)

The entire agent lives in `agent.py` with this execution flow:

1. **Configuration** (lines 1-300): Constants for watchlist companies, keywords, trigger lists, regulatory source URLs, and industry-specific award monitoring
2. **Data Collection** (lines 300-800): Functions that scrape/fetch from 9+ Australian legal sources (ASIC, ACCC, AustLII, Federal Court, Supreme Courts, PPSR, Google News RSS)
3. **Deduplication** (lines 780-815): `load_seen_articles()` / `save_seen_articles()` using `seen_articles.json`
4. **News Aggregation** (lines 816-1000): `fetch_australian_legal_news()` runs ~20 targeted RSS searches with rate-limiting (`time.sleep(0.5)`)
5. **AI Analysis** (lines 1000-1400): `generate_briefing()` assembles all data and sends to Claude (`claude-sonnet-4-20250514`) with a detailed employment law prompt
6. **Delivery** (lines 1400-1650): HTML email formatting and SMTP sending
7. **Entry point** (lines 1648-1682): `if __name__ == "__main__"` block

### Key functions

| Function | Purpose |
|---|---|
| `fetch_asic_media_releases()` | ASIC regulatory releases |
| `fetch_accc_news()` | ACCC competition announcements |
| `fetch_austlii_recent_cases()` | AustLII legal case search |
| `fetch_asic_published_notices()` | Director changes, appointments |
| `search_federal_court_filings()` | Winding up, statutory demands |
| `search_supreme_courts()` | NSW/VIC insolvency matters |
| `search_watchlist_in_courts()` | Monitor specific companies in court filings |
| `search_ppsr_indicators()` | Personal Property Securities Register |
| `fetch_google_news_rss()` | Google News RSS with date filtering |
| `search_watchlist_companies()` | Monitor watchlist companies in news |
| `fetch_australian_legal_news()` | Main aggregator - calls all news sources |
| `generate_briefing()` | Core function - collects all data, calls Claude API |
| `format_briefing_html()` | Converts markdown briefing to styled HTML email |
| `save_briefing()` | Writes briefing to `briefing_YYYY-MM-DD.txt` |
| `send_email()` | SMTP email delivery with HTML + plaintext |

### Data flow

```
External Sources (ASIC, ACCC, Courts, RSS)
    → Data Collection Functions
    → Deduplication (seen_articles.json)
    → Aggregation (fetch_australian_legal_news)
    → AI Analysis (Claude claude-sonnet-4-20250514 via generate_briefing)
    → Output: briefing_*.txt file + HTML email
```

## Development Workflow

### Setup

```bash
pip install -r requirements.txt
```

Dependencies: `anthropic`, `requests`, `beautifulsoup4`, `python-dotenv`, `lxml`

### Running the agent

```bash
# Requires ANTHROPIC_API_KEY environment variable
export ANTHROPIC_API_KEY="sk-..."
python agent.py
```

Output: `briefing_YYYY-MM-DD.txt` in the working directory.

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API authentication |
| `EMAIL_TO` | For email delivery | Recipient email address |
| `EMAIL_FROM` | For email delivery | Sender email address |
| `EMAIL_PASSWORD` | For email delivery | SMTP password |
| `SMTP_SERVER` | For email delivery | SMTP server hostname |
| `SMTP_PORT` | For email delivery | SMTP port (default: 587) |

### CI/CD

- **GitHub Actions**: `daily-briefing.yml` runs Mon-Fri at 6:00 AM AEST (cron: `0 20 * * 0-4` UTC)
- **Manual trigger**: Supports `workflow_dispatch` with optional branch input
- **Artifacts**: Briefing files and `seen_articles.json` retained for 90 days
- **Runner**: `ubuntu-22.04`, Python 3.11, 30-minute timeout

## Code Conventions

### Style

- No linter or formatter configured (no flake8, black, pylint, etc.)
- Single-file architecture - all logic in `agent.py`
- Section separators use `# ===...===` comment blocks
- Functions use docstrings for high-level documentation
- Print statements used for logging (no logging module)
- Error handling uses bare `except:` in some places and `except Exception as e:` in others

### Patterns

- **Rate limiting**: `time.sleep(0.5)` between external HTTP requests
- **Graceful degradation**: Data collection functions return empty dicts/lists on failure
- **Deduplication**: Title-based tracking via JSON file with 14-day retention window
- **Constants at module level**: Watchlist companies, keywords, and trigger lists are defined as module-level lists/dicts

### Data storage

- **No database** - all persistence is JSON file-based
- `seen_articles.json` - article dedup (gitignored)
- `briefing_*.txt` - daily output files (gitignored)
- `source_performance.json` - performance metrics (gitignored)
- `error_log.txt` - error log (gitignored)

## Important Notes for AI Assistants

### Do not commit

- `.env` files or any file containing API keys/credentials
- `briefing_*.txt` output files
- `seen_articles.json`
- `source_performance.json`
- `error_log.txt`

### Testing

- **No automated test suite exists** - there are no test files, pytest config, or test framework
- Manual testing via `python agent.py` (requires API key and network access)
- API endpoint testing via curl (if Flask landing page server is running)

### When modifying `agent.py`

- The file is ~1,680 lines - be careful with context when making changes
- Configuration constants are at the top (lines 1-300)
- Data collection functions are in the middle (300-800)
- The Claude API call is in `generate_briefing()` around line 1198
- The prompt template is large (~200 lines) and embedded in `generate_briefing()`
- Entry point is at the bottom (line 1648)
- Adding new data sources: follow the pattern in `fetch_australian_legal_news()` - add a new search, extend `all_news`, add `time.sleep(0.5)`
- Adding new watchlist companies: append to `WATCHLIST_COMPANIES` list with an industry comment

### When modifying the CI workflow

- Secrets are configured in GitHub repository settings
- The cron schedule uses UTC times (AEST = UTC+10)
- `continue-on-error: false` means the workflow fails on any step error
- Artifacts upload runs with `if: always()` to capture output even on failure
