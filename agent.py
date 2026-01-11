"""
Australian Legal Intelligence Agent
Generates daily briefings on legal matters, regulatory actions, and business opportunities
"""

import anthropic
import requests
from datetime import datetime, timedelta
import os
import json
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parsedate_to_datetime

# Companies to monitor closely (watchlist)
WATCHLIST_COMPANIES = [
    'Aussie Broadband',
    'British Solar Renewables',
    'Macquarie Bank',
    'Next DC',
    'Prospa',
    'Wingate',
    'La Salle',
    'Brookfield',
    'Egis',
    'Waveconn',
    'Scentia',
    'Abergeldie Complex Infrastructure',
    'CPB Contractors',
    'Jacaranda',
    'Team Global Express',
    'St Vincents Health Australia',
    'Northern Star Resources',
    'Blackstone',
    'KKR',
    'Firefly Metals',
    'Cygnus Metals',
    'Greencross',
    'Bondi Brands',
    'Aula Energy',
    'ContiTech',
    'UGL',
    'David Jones',
    'Independent Reserve',
    'CoinSpot',
    'Asahi',
    'Downer EDI'
]

# Industries to monitor closely
PRIORITY_INDUSTRIES = [
    'Construction',
    'Retail',
    'Financial Services',
    'Mining',
    'Technology',
    'Transport',
    'Energy',
    'Hospitality',
    'Real Estate'
]

# Minimum company size (by revenue/employees) to flag
MIN_COMPANY_SIZE = {
    'revenue': 10_000_000,  # $10M annual revenue
    'employees': 50
}

# Keywords that indicate high-value matters
HIGH_VALUE_KEYWORDS = [
    'class action',
    'regulatory investigation',
    'ASIC proceedings',
    'ACCC action',
    'administration',
    'receivership',
    'winding up',
    'liquidation',
    'insolvent trading',
    'director penalty',
    'AML',
    'CTF'

]

# Your firm's conflict check - companies to exclude from briefings
EXCLUDED_COMPANIES = [
    # Add ACNs or company names of existing clients to avoid conflicts
    # Example: "Client Company Pty Ltd ACN 987654321",
]


def fetch_asic_media_releases():
    """Fetch recent ASIC media releases"""
    try:
        url = "https://asic.gov.au/about-asic/news-centre/news-items/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        releases = []

        # Find news items (adjust selectors based on actual ASIC site structure)
        news_items = soup.find_all('article', limit=10) or soup.find_all('div', class_='news-item', limit=10)

        for item in news_items[:10]:
            title_elem = item.find(['h2', 'h3', 'h4', 'a'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                date_elem = item.find(['time', 'span'], class_=lambda x: x and 'date' in x.lower() if x else False)
                releases.append({
                    'title': title,
                    'date': date_elem.get_text(strip=True) if date_elem else 'Recent'
                })

        return {"releases": releases, "count": len(releases)}

    except Exception as e:
        print(f"Error fetching ASIC data: {e}")
        return {"releases": [], "count": 0, "error": str(e)}


def fetch_accc_news():
    """Fetch recent ACCC media releases and enforcement actions"""
    try:
        url = "https://www.accc.gov.au/media-and-publications/media-releases"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        releases = []

        # Find media release items
        news_items = soup.find_all(['article', 'div'], class_=lambda x: x and 'media' in x.lower() if x else False, limit=10)
        if not news_items:
            news_items = soup.find_all('article', limit=10)

        for item in news_items[:10]:
            title_elem = item.find(['h2', 'h3', 'h4', 'a'])
            if title_elem:
                releases.append({
                    'title': title_elem.get_text(strip=True)
                })

        return {"releases": releases, "count": len(releases)}

    except Exception as e:
        print(f"Error fetching ACCC data: {e}")
        return {"releases": [], "count": 0, "error": str(e)}


def fetch_austlii_recent_cases():
    """Fetch recent cases from AustLII (Australasian Legal Information Institute)"""
    try:
        # AustLII Federal Court recent decisions
        url = "http://www.austlii.edu.au/cgi-bin/viewdb/au/cases/cth/FCA/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        cases = []

        # Find case links (AustLII has a specific structure)
        links = soup.find_all('a', href=True, limit=15)

        for link in links[:15]:
            text = link.get_text(strip=True)
            # Filter for case citations (typically contain year and numbers)
            if any(char.isdigit() for char in text) and len(text) > 5:
                cases.append({
                    'title': text,
                    'court': 'Federal Court of Australia'
                })

        return {"cases": cases, "count": len(cases)}

    except Exception as e:
        print(f"Error fetching AustLII data: {e}")
        return {"cases": [], "count": 0, "error": str(e)}


def fetch_google_news_rss(query, max_results=10, max_age_days=7, time_range='7d'):
    """Fetch news from Google News RSS feed with date filtering

    Args:
        query: Search query
        max_results: Maximum number of results to return
        max_age_days: Maximum age of articles in days (for post-filtering)
        time_range: Google News time range parameter: '1h', '1d', '7d', '1m'
    """
    try:
        # Add time range to query to tell Google News to only return recent articles
        time_filtered_query = f"{query} when:{time_range}"

        # Google News RSS URL with Australian localization
        rss_url = f"https://news.google.com/rss/search?q={time_filtered_query.replace(' ', '+')}&hl=en-AU&gl=AU&ceid=AU:en"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(rss_url, headers=headers, timeout=15)
        response.raise_for_status()

        # Parse XML RSS feed
        soup = BeautifulSoup(response.content, 'xml')
        articles = []
        now = datetime.now(datetime.now().astimezone().tzinfo)

        # Find all item elements (fetch more to account for filtering)
        items = soup.find_all('item', limit=max_results * 2)

        for item in items:
            title_elem = item.find('title')
            pubdate_elem = item.find('pubDate')
            link_elem = item.find('link')

            if title_elem:
                # Parse publication date and calculate age
                age_days = None
                time_category = 'unknown'

                if pubdate_elem:
                    try:
                        pub_datetime = parsedate_to_datetime(pubdate_elem.get_text(strip=True))
                        age_days = (now - pub_datetime).days

                        # Categorize by age
                        if age_days <= 1:
                            time_category = '24h'
                        elif age_days <= 7:
                            time_category = '7d'
                        elif age_days <= 30:
                            time_category = '30d'
                        else:
                            time_category = 'old'

                        # Skip articles older than max_age_days
                        if age_days > max_age_days:
                            continue

                    except Exception as e:
                        # If date parsing fails, skip the article to be safe
                        continue

                articles.append({
                    'title': title_elem.get_text(strip=True),
                    'source': 'Google News',
                    'published': pubdate_elem.get_text(strip=True) if pubdate_elem else 'Recent',
                    'link': link_elem.get_text(strip=True) if link_elem else '',
                    'age_days': age_days,
                    'time_category': time_category
                })

        # Sort by age (newest first) and limit to max_results
        articles.sort(key=lambda x: x.get('age_days', 999))
        articles = articles[:max_results]

        return {"articles": articles, "count": len(articles)}

    except Exception as e:
        print(f"Error fetching Google News for '{query}': {e}")
        return {"articles": [], "count": 0, "error": str(e)}


def search_watchlist_companies():
    """Search for news about ALL watchlist companies - SIMPLE GENERAL GOOGLE NEWS SEARCHES"""
    company_news = []

    print(f"  Searching for all {len(WATCHLIST_COMPANIES)} watchlist companies (latest news)...")

    for i, company in enumerate(WATCHLIST_COMPANIES, 1):
        if company:
            try:
                # SIMPLE Google News search - just company name + latest filter
                # Using multiple simple variations to maximize coverage
                queries = [
                    f'{company} news australia',  # General news search
                    f'{company} business',  # Business news
                    f'{company} australia',  # General Australia search
                ]

                company_articles = []
                for query in queries:
                    # Get latest news (7 days) for each query
                    results = fetch_google_news_rss(query, max_results=5, max_age_days=7, time_range='7d')
                    company_articles.extend(results.get('articles', []))
                    time.sleep(0.3)  # Rate limiting between queries

                # Deduplicate by title
                seen_titles = set()
                unique_articles = []
                for article in company_articles:
                    title = article.get('title', '')
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        unique_articles.append(article)

                if len(unique_articles) > 0:
                    # Show age breakdown
                    age_24h = sum(1 for a in unique_articles if a.get('time_category') == '24h')
                    age_7d = sum(1 for a in unique_articles if a.get('time_category') == '7d')

                    print(f"    [{i}/{len(WATCHLIST_COMPANIES)}] {company}: {len(unique_articles)} articles (24h:{age_24h} 7d:{age_7d})")
                    company_news.extend(unique_articles[:10])  # Increased to top 10 per company
                else:
                    print(f"    [{i}/{len(WATCHLIST_COMPANIES)}] {company}: No news (last 7 days)")

                time.sleep(0.2)  # Rate limiting between companies

            except Exception as e:
                print(f"    Error searching for {company}: {e}")
                continue

    return {"articles": company_news, "count": len(company_news)}


def fetch_australian_legal_news():
    """Aggregate Australian legal news from multiple sources using Google News RSS with latest time filtering"""
    all_news = []

    # GENERAL MARKET THEMES - LATEST NEWS (Last 7 days)

    # 0. Latest Australian business news (general scan)
    print("  - Latest Australian business news (7d)...")
    aus_business = fetch_google_news_rss("australia business news", max_results=15, max_age_days=7, time_range='7d')
    all_news.extend(aus_business.get('articles', []))
    time.sleep(0.5)

    # 0a. Latest Australian corporate news
    print("  - Latest Australian corporate news (7d)...")
    aus_corporate = fetch_google_news_rss("australia corporate news ASX", max_results=15, max_age_days=7, time_range='7d')
    all_news.extend(aus_corporate.get('articles', []))
    time.sleep(0.5)

    # 1. Class actions and litigation (LATEST)
    print("  - Class actions & litigation (latest 7d)...")
    class_action_results = fetch_google_news_rss("australia class action litigation court", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(class_action_results.get('articles', []))
    time.sleep(0.5)

    # 2. Insolvency and restructuring - LATEST
    print("  - Insolvency & restructuring (latest 7d)...")
    insolvency_results = fetch_google_news_rss("australia insolvency administration liquidation receivership", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(insolvency_results.get('articles', []))
    time.sleep(0.5)

    # 2a. State-based insolvency appointments (LATEST)
    print("  - State insolvency appointments (latest 7d)...")
    state_insolvency = fetch_google_news_rss("australia appointed administrator receiver liquidator", max_results=8, max_age_days=7, time_range='7d')
    all_news.extend(state_insolvency.get('articles', []))
    time.sleep(0.5)

    # 2b. Voluntary administration and DOCA (LATEST)
    print("  - Voluntary administration (latest 7d)...")
    va_results = fetch_google_news_rss("australia voluntary administration DOCA", max_results=8, max_age_days=7, time_range='7d')
    all_news.extend(va_results.get('articles', []))
    time.sleep(0.5)

    # 3. Supreme Court winding up applications (LATEST)
    print("  - Supreme Court winding up (latest 7d)...")
    supreme_court_results = fetch_google_news_rss("australia supreme court winding up", max_results=8, max_age_days=7, time_range='7d')
    all_news.extend(supreme_court_results.get('articles', []))
    time.sleep(0.5)

    # 4. ASIC enforcement and regulatory (LATEST)
    print("  - ASIC enforcement (latest 7d)...")
    asic_results = fetch_google_news_rss("australia ASIC enforcement investigation", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(asic_results.get('articles', []))
    time.sleep(0.5)

    # 4a. ASIC banning orders and disqualifications (LATEST)
    print("  - ASIC bans & disqualifications (latest 7d)...")
    asic_bans = fetch_google_news_rss("australia ASIC banned disqualified director", max_results=8, max_age_days=7, time_range='7d')
    all_news.extend(asic_bans.get('articles', []))
    time.sleep(0.5)

    # 5. ACCC and competition law (LATEST)
    print("  - ACCC & competition (latest 7d)...")
    accc_results = fetch_google_news_rss("australia ACCC enforcement competition consumer", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(accc_results.get('articles', []))
    time.sleep(0.5)

    # 6. Corporate disputes and M&A (LATEST)
    print("  - Corporate disputes (latest 7d)...")
    corporate_results = fetch_google_news_rss("australia corporate dispute merger acquisition", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(corporate_results.get('articles', []))
    time.sleep(0.5)

    # 7. Director liability and governance (LATEST)
    print("  - Director liability (latest 7d)...")
    director_results = fetch_google_news_rss("australia director liability governance breach", max_results=8, max_age_days=7, time_range='7d')
    all_news.extend(director_results.get('articles', []))
    time.sleep(0.5)

    # 7a. Director resignations (LATEST)
    print("  - Director resignations (latest 7d)...")
    director_resign = fetch_google_news_rss("australia director resigned stepping down", max_results=8, max_age_days=7, time_range='7d')
    all_news.extend(director_resign.get('articles', []))
    time.sleep(0.5)

    # 8. Trading while insolvent and phoenix activity (LATEST)
    print("  - Insolvent trading (latest 7d)...")
    insolvent_trading = fetch_google_news_rss("australia insolvent trading phoenix director penalty", max_results=8, max_age_days=7, time_range='7d')
    all_news.extend(insolvent_trading.get('articles', []))
    time.sleep(0.5)

    # WATCHLIST COMPANIES (all 31 companies - LATEST 7 days)
    print("  - Watchlist company news (all 31 companies, latest 7d)...")
    watchlist_results = search_watchlist_companies()
    all_news.extend(watchlist_results.get('articles', []))

    print(f"\n  Total articles collected: {len(all_news)}")

    # Deduplicate all articles by title before returning
    seen_titles = set()
    unique_all_news = []
    for article in all_news:
        title = article.get('title', '')
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_all_news.append(article)

    print(f"  After deduplication: {len(unique_all_news)} unique articles")

    return {
        "articles": unique_all_news[:150],  # Increased limit for comprehensive coverage
        "count": len(unique_all_news[:150])
    }


def fetch_asic_data():
    """Fetch all ASIC-related data"""
    return fetch_asic_media_releases()


def generate_briefing():
    """Generate the daily legal intelligence briefing"""
    print("Fetching data from Australian legal sources...")

    # Collect data from multiple sources
    print("- Fetching ASIC media releases...")
    asic_data = fetch_asic_data()

    print("- Fetching ACCC announcements...")
    accc_data = fetch_accc_news()

    print("- Fetching recent cases from AustLII...")
    austlii_data = fetch_austlii_recent_cases()

    print("- Searching for Australian legal news...")
    news_data = fetch_australian_legal_news()

    # Prepare data summary for Claude
    watchlist_str = "\n".join([f"- {company}" for company in WATCHLIST_COMPANIES if company])
    industries_str = ", ".join(PRIORITY_INDUSTRIES)
    keywords_str = ", ".join(HIGH_VALUE_KEYWORDS)

    # Debug: Print data collection results
    print(f"\nData Collection Summary:")
    print(f"  ASIC releases: {asic_data.get('count', 0)}")
    print(f"  ACCC releases: {accc_data.get('count', 0)}")
    print(f"  AustLII cases: {austlii_data.get('count', 0)}")
    print(f"  News articles: {news_data.get('count', 0)}")
    print(f"  Total data points: {asic_data.get('count', 0) + accc_data.get('count', 0) + austlii_data.get('count', 0) + news_data.get('count', 0)}\n")

    # Format ASIC releases
    asic_releases_str = "\n".join([
        f"- {r.get('title', 'No title')} ({r.get('date', 'Recent')})"
        for r in asic_data.get('releases', [])[:10]
    ]) or "No recent ASIC releases found"

    # Format ACCC releases
    accc_releases_str = "\n".join([
        f"- {r.get('title', 'No title')}"
        for r in accc_data.get('releases', [])[:10]
    ]) or "No recent ACCC releases found"

    # Format AustLII cases
    austlii_cases_str = "\n".join([
        f"- {c.get('title', 'No title')} ({c.get('court', 'Unknown court')})"
        for c in austlii_data.get('cases', [])[:10]
    ]) or "No recent cases found"

    # Categorize and format news articles by age (LATEST 7 DAYS ONLY)
    articles_24h = [a for a in news_data.get('articles', []) if a.get('time_category') == '24h']
    articles_7d = [a for a in news_data.get('articles', []) if a.get('time_category') == '7d']

    print(f"  Article breakdown: 24h={len(articles_24h)}, 7d={len(articles_7d)}")

    news_articles_str = "LAST 24 HOURS (IMMEDIATE OPPORTUNITIES):\n"
    news_articles_str += "\n".join([f"- {a.get('title', 'No title')}" for a in articles_24h[:30]]) or "No articles in last 24 hours\n"

    news_articles_str += "\n\nLAST 2-7 DAYS (RECENT DEVELOPMENTS):\n"
    news_articles_str += "\n".join([f"- {a.get('title', 'No title')}" for a in articles_7d[:30]]) or "No articles from 2-7 days ago"

    data_summary = f"""
DATA COLLECTED FROM AUSTRALIAN SOURCES:

ASIC Media Releases ({asic_data.get('count', 0)} items):
{asic_releases_str}

ACCC Announcements ({accc_data.get('count', 0)} items):
{accc_releases_str}

Recent Federal Court Cases from AustLII ({austlii_data.get('count', 0)} cases):
{austlii_cases_str}

Australian Legal News ({news_data.get('count', 0)} articles):
{news_articles_str}

MONITORING PRIORITIES:
Watchlist Companies ({len([c for c in WATCHLIST_COMPANIES if c.strip()])} companies):
{watchlist_str}

Priority Industries: {industries_str}
High-Value Keywords: {keywords_str}
    """

    # Call Claude to analyze and generate briefing
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": f"""You are a legal intelligence analyst for an Australian commercial law firm specializing in disputes, insolvency, and regulatory matters.

Analyze this data from {datetime.now().strftime('%B %d, %Y')} (Australian sources):

{data_summary}

CRITICAL INSTRUCTIONS - LATEST NEWS ONLY:
- ALL articles are from the LAST 7 DAYS maximum (nothing older)
- Articles are categorized: "LAST 24 HOURS" and "LAST 2-7 DAYS"
- **IMMEDIATE OPPORTUNITIES**: Prioritize "LAST 24 HOURS" section
- **RECENT DEVELOPMENTS**: Use "LAST 2-7 DAYS" section
- Every article is fresh and current - treat all as actionable intelligence
- Pay special attention to ANY mentions of our watchlist companies
- Cross-reference news items with our priority industries and keywords

Generate a concise morning briefing with:

## Executive Summary
Provide 2-3 sentences highlighting the most significant developments from the last 7 days.
Prioritize anything from the last 24 hours.

## High-Priority Opportunities (This Week)
List specific matters worth pursuing from the data:
 - Class actions (existing or potential)
 - ASIC/ACCC regulatory investigations
 - Insolvency and restructuring matters
 - Director liability issues
 - Major commercial disputes

Prioritize opportunities from "LAST 24 HOURS" section. All news is current and actionable.

## Watchlist Company Activity
Specifically identify ANY mentions of our {len(WATCHLIST_COMPANIES)} watchlist companies.
Note: Even tangential mentions (industry news affecting these companies) are valuable.
If none found, state this clearly and suggest targeted monitoring.

## Priority Industry Developments
Analyze news related to our priority industries: {industries_str}
Identify potential opportunities or risks in these sectors.

## Emerging Trends
Identify patterns across Australian industries, regulators (ASIC, ACCC, etc.), or claim types.
Consider broader market conditions affecting our practice areas.

## Action Items
Provide specific, actionable next steps:
 - Companies to research further
 - Potential clients to contact
 - Regulatory developments to monitor
 - Market intelligence to gather

Be direct and practical - this briefing drives business development decisions."""
        }]
    )

    return message.content[0].text


def save_briefing(briefing_content):
    """Save briefing to file"""
    timestamp = datetime.now().strftime('%Y-%m-%d')
    filename = f'briefing_{timestamp}.txt'

    with open(filename, 'w') as f:
        f.write(f"Australian Legal Intelligence Briefing - {timestamp}\n")
        f.write("=" * 70 + "\n\n")
        f.write(briefing_content)

    print(f"Briefing saved to {filename}")
    return filename


def send_email(briefing_content, filename):
    """Send briefing via email"""
    try:
        # Get email configuration from environment variables
        email_to = os.environ.get('EMAIL_TO')
        email_from = os.environ.get('EMAIL_FROM')
        email_password = os.environ.get('EMAIL_PASSWORD')
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))

        # Check if email is configured
        if not all([email_to, email_from, email_password, smtp_server]):
            print("Email not configured - skipping email send")
            print(f"  EMAIL_TO: {'✓' if email_to else '✗'}")
            print(f"  EMAIL_FROM: {'✓' if email_from else '✗'}")
            print(f"  EMAIL_PASSWORD: {'✓' if email_password else '✗'}")
            print(f"  SMTP_SERVER: {'✓' if smtp_server else '✗'}")
            return False

        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Australian Legal Intelligence Briefing - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = email_from
        msg['To'] = email_to

        # Plain text version
        text_content = briefing_content

        # HTML version with better formatting
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1 {{ color: #1a1a1a; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
                h2 {{ color: #0066cc; margin-top: 20px; }}
                ul {{ margin-left: 20px; }}
                .highlight {{ background-color: #fff3cd; padding: 2px 5px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <pre style="font-family: Arial, sans-serif; white-space: pre-wrap; word-wrap: break-word;">{briefing_content}</pre>
            <div class="footer">
                <p>Australian Legal Intelligence Briefing - Automated Daily Report</p>
                <p>Generated: {datetime.now().strftime('%B %d, %Y at %H:%M AEST')}</p>
            </div>
        </body>
        </html>
        """

        # Attach both versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        print(f"Sending email to {email_to}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_from, email_password)
            server.send_message(msg)

        print(f"✓ Email sent successfully to {email_to}")
        return True

    except Exception as e:
        print(f"✗ Error sending email: {e}")
        return False


if __name__ == "__main__":
    print("Generating Australian Legal Intelligence Briefing...")
    print(f"Monitoring {len([c for c in WATCHLIST_COMPANIES if c.strip()])} companies")
    print(f"Focus industries: {', '.join(PRIORITY_INDUSTRIES[:3])}...")

    try:
        # Generate briefing
        briefing = generate_briefing()

        # Save to file
        filename = save_briefing(briefing)

        # Send via email
        email_sent = send_email(briefing, filename)

        # Display preview
        print("\n" + "=" * 70)
        print("BRIEFING PREVIEW")
        print("=" * 70)
        print(briefing)
        print("=" * 70)
        print(f"\nBriefing generated successfully: {filename}")

        if email_sent:
            print("✓ Email delivered successfully")
        else:
            print("⚠ Email not sent (check configuration)")

    except Exception as e:
        print(f"Error generating briefing: {e}")
        raise
