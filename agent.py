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


def search_legal_news(query="australian legal news insolvency regulatory"):
    """Search for Australian legal news using public search"""
    try:
        # Using DuckDuckGo HTML search (no API key required)
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        results = []

        # Find search result links
        result_links = soup.find_all('a', class_='result__a', limit=10)

        for link in result_links[:10]:
            title = link.get_text(strip=True)
            if title and len(title) > 10:
                results.append({
                    'title': title,
                    'source': 'Web Search'
                })

        return {"articles": results, "count": len(results)}

    except Exception as e:
        print(f"Error searching legal news: {e}")
        return {"articles": [], "count": 0, "error": str(e)}


def search_watchlist_companies():
    """Search for news about specific watchlist companies"""
    company_news = []

    # Extract actual company names (remove comments)
    active_companies = [c.strip().lstrip('#').strip() for c in WATCHLIST_COMPANIES if c.strip() and not c.strip().startswith('#')]

    print(f"  Searching for {len(active_companies)} watchlist companies...")

    for company in active_companies[:10]:  # Limit to first 10 to avoid rate limiting
        if company:
            try:
                results = search_legal_news(f"{company} australia legal news")
                company_news.extend(results.get('articles', []))
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"  Error searching for {company}: {e}")
                continue

    return {"articles": company_news, "count": len(company_news)}


def fetch_australian_legal_news():
    """Aggregate Australian legal news from multiple sources"""
    all_news = []

    # Search for general Australian legal news
    print("  - General legal news...")
    news_results = search_legal_news("australian legal news class action ASIC ACCC")
    all_news.extend(news_results.get('articles', []))

    time.sleep(1)  # Rate limiting

    # Search for insolvency news
    print("  - Insolvency news...")
    insolvency_results = search_legal_news("australian insolvency administration liquidation")
    all_news.extend(insolvency_results.get('articles', []))

    time.sleep(1)  # Rate limiting

    # Search for regulatory enforcement
    print("  - Regulatory enforcement...")
    regulatory_results = search_legal_news("ASIC ACCC enforcement action australia")
    all_news.extend(regulatory_results.get('articles', []))

    time.sleep(1)  # Rate limiting

    # Search for watchlist companies
    print("  - Watchlist company news...")
    watchlist_results = search_watchlist_companies()
    all_news.extend(watchlist_results.get('articles', []))

    return {
        "articles": all_news[:30],  # Increased limit to 30 results
        "count": len(all_news[:30])
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

    # Format news articles
    news_articles_str = "\n".join([
        f"- {article.get('title', 'No title')}"
        for article in news_data.get('articles', [])[:15]
    ]) or "No recent legal news found"

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

IMPORTANT INSTRUCTIONS:
- Pay special attention to ANY mentions of our watchlist companies
- Even if data is limited, provide strategic insights based on what IS available
- Cross-reference news items with our priority industries and keywords
- Identify potential opportunities even in general legal news
- If specific company data is scarce, note this and suggest proactive monitoring approaches

Generate a concise morning briefing with:

## Executive Summary
Provide 2-3 sentences highlighting the most significant developments. If limited data, summarize what WAS found and note key gaps requiring further monitoring.

## High-Priority Opportunities
List specific matters worth pursuing from the data above:
 - Class actions (existing or potential)
 - ASIC/ACCC regulatory investigations
 - Insolvency and restructuring matters
 - Director liability issues
 - Major commercial disputes

If no specific opportunities found, suggest areas to monitor based on industry trends.

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


if __name__ == "__main__":
    print("Generating Australian Legal Intelligence Briefing...")
    print(f"Monitoring {len([c for c in WATCHLIST_COMPANIES if c.strip()])} companies")
    print(f"Focus industries: {', '.join(PRIORITY_INDUSTRIES[:3])}...")

    try:
        briefing = generate_briefing()
        filename = save_briefing(briefing)

        print("\n" + "=" * 70)
        print("BRIEFING PREVIEW")
        print("=" * 70)
        print(briefing)
        print("=" * 70)
        print(f"\nBriefing generated successfully: {filename}")

    except Exception as e:
        print(f"Error generating briefing: {e}")
        raise
