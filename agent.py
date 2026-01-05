"""
Australian Legal Intelligence Agent
Generates daily briefings on legal matters, regulatory actions, and business opportunities
"""

import anthropic
import requests
from datetime import datetime, timedelta
import os
import json

# Companies to monitor closely (watchlist)
WATCHLIST_COMPANIES = [
    # Aussie Broadband
    # British Solar Renewables
    # Macquarie Bank
    # Next DC
    # Prospa
    # Wingate
    # La Salle
    # Brookfield
    # Egis
    # Waveconn
    # Scentia
    # Abergeldie Comlex Infrastructure
    # CPB Contractors
    # Jacaranda
    # Team Global Exrpress
    # St Vincents Health Australia
    # Northern Star Resoources
    # Blackstone
    # KKR
    # Firefly Metals
    # Cygnus Metals
    # Greencross
    # Bondi Brands
    # Aula Energy
    # ContiTech
    # UGL
    # David Jones
    # Independent Reserve
    # CoinSpot
    # Asahi
    # Downer EDI
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


def fetch_asic_data():
    """Fetch recent ASIC notices and regulatory actions"""
    try:
        # Note: This is a placeholder. ASIC doesn't have a public API
        # You would need to scrape their website or use a legal data provider
        return {
            "notices": [],
            "note": "ASIC data scraping requires implementation"
        }
    except Exception as e:
        return {"notices": [], "error": str(e)}


def fetch_australian_legal_news():
    """Fetch Australian legal news from various sources"""
    # Placeholder for legal news aggregation
    # In production, you would scrape/API from:
    # - Australasian Legal Information Institute (AustLII)
    # - Law Society publications
    # - AFR Legal section
    # - The Australian legal news
    return {
        "articles": [
            "Placeholder: Australian legal news would be fetched here"
        ]
    }


def generate_briefing():
    """Generate the daily legal intelligence briefing"""
    # Collect data
    asic_data = fetch_asic_data()
    news_data = fetch_australian_legal_news()

    # Prepare data summary for Claude
    watchlist_str = "\n".join([f"- {company}" for company in WATCHLIST_COMPANIES if company.strip()])
    industries_str = ", ".join(PRIORITY_INDUSTRIES)
    keywords_str = ", ".join(HIGH_VALUE_KEYWORDS)

    data_summary = f"""
    ASIC Notices (Last 24h): {len(asic_data.get('notices', []))} new items

    Australian Legal News:
    {chr(10).join(f"- {article}" for article in news_data.get('articles', []))}

    MONITORING PRIORITIES:
    Watchlist Companies: {len([c for c in WATCHLIST_COMPANIES if c.strip()])} companies
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

Generate a concise morning briefing with:

## Executive Summary
[2-3 sentences on most significant Australian legal developments]

## High-Priority Opportunities
[Ranked list of matters worth pursuing - focus on:
 - Class actions
 - ASIC/ACCC regulatory investigations
 - Insolvency and restructuring matters
 - Director liability issues
 - Major commercial disputes
]

## Watchlist Activity
[Any mentions or developments related to our monitored companies and industries]

## Emerging Trends
[Patterns across Australian industries, regulators (ASIC, ACCC, etc.), or claim types]

## Action Items
[Specific next steps for business development and client engagement]

Be specific about company names, amounts, and Australian jurisdictions when available.
Focus on matters likely to be valuable for a commercial disputes and insolvency practice."""
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
