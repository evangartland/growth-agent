"""
Australian Employment Law Intelligence Agent
Generates daily briefings on employment law matters, adverse action triggers, and advisory opportunities
Focus: Adverse action claims, whistleblowing, restructures, modern awards
Target Industries: Retail, Construction, Healthcare, Manufacturing, Financial Services
"""

import anthropic
import requests
from datetime import datetime, timedelta
import os
import json
from bs4 import BeautifulSoup
import time
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parsedate_to_datetime

# ============================================================================
# EMPLOYMENT LAW FOCUS CONFIGURATION
# ============================================================================

# Major employers in target industries to monitor for employment law triggers
WATCHLIST_COMPANIES = [
    # RETAIL (high adverse action risk due to casual workforce, award complexity)
    'Woolworths',
    'Coles',
    'Wesfarmers',
    'JB Hi-Fi',
    'Harvey Norman',
    'Bunnings',
    'Kmart',
    'Target',
    'Myer',
    'David Jones',
    'Super Retail Group',
    'Premier Investments',
    'Accent Group',
    'Country Road',
    'Cotton On',

    # CONSTRUCTION (restructures, subcontractor issues, safety whistleblowing)
    'CIMIC Group',
    'Lendlease',
    'Downer EDI',
    'CPB Contractors',
    'John Holland',
    'Multiplex',
    'Probuild',
    'Built',
    'Roberts Co',
    'Hansen Yuncken',
    'Mirvac',
    'Stockland',
    'Metricon',
    'Simonds Homes',
    'Hutchinson Builders',

    # HEALTHCARE (whistleblowing, award compliance, staff shortages)
    'Ramsay Health Care',
    'Healthscope',
    'Healius',
    'Australian Clinical Labs',
    'Sonic Healthcare',
    'St Vincents Health',
    'Epworth Healthcare',
    'Calvary Health Care',
    'Bupa',
    'Regis Healthcare',
    'Estia Health',
    'Japara Healthcare',
    'Opal Aged Care',
    'Bolton Clarke',
    'Uniting',

    # MANUFACTURING (restructures, redundancies, award modernisation)
    'BlueScope Steel',
    'Boral',
    'CSR Limited',
    'Amcor',
    'Orora',
    'Pact Group',
    'Visy',
    'GUD Holdings',
    'Reece Limited',
    'Rheem Australia',
    'Toyota Australia',
    'Holden',
    'Arnott\'s',
    'Lion',
    'Asahi',

    # FINANCIAL SERVICES (whistleblowing, restructures, regulatory pressure)
    'Commonwealth Bank',
    'Westpac',
    'NAB',
    'ANZ',
    'Macquarie Group',
    'AMP',
    'IOOF',
    'Insignia Financial',
    'Suncorp',
    'QBE',
    'IAG',
    'Medibank',
    'NIB',
    'Australian Super',
    'REST Super'
]

# Target industries for employment law services
PRIORITY_INDUSTRIES = [
    'Retail',
    'Construction',
    'Healthcare',
    'Manufacturing',
    'Financial Services'
]

# Minimum company size (by revenue/employees) to flag
MIN_COMPANY_SIZE = {
    'revenue': 50_000_000,  # $50M annual revenue
    'employees': 200  # Significant workforce
}

# ============================================================================
# EMPLOYMENT LAW TRIGGER KEYWORDS
# ============================================================================

# Keywords that indicate high-value employment law matters
HIGH_VALUE_KEYWORDS = [
    # ADVERSE ACTION TRIGGERS
    'adverse action',
    'general protections',
    'workplace rights',
    'unlawful termination',
    'unfair dismissal',
    'constructive dismissal',
    'discrimination',
    'harassment',
    'bullying',
    'victimisation',

    # WHISTLEBLOWING TRIGGERS
    'whistleblower',
    'whistleblowing',
    'protected disclosure',
    'public interest disclosure',
    'speaking out',
    'retaliation',
    'reprisal',

    # RESTRUCTURE TRIGGERS
    'restructure',
    'restructuring',
    'redundancy',
    'redundancies',
    'job cuts',
    'layoffs',
    'downsizing',
    'workforce reduction',
    'cost cutting',
    'efficiency review',
    'organisational change',
    'transformation',

    # MODERN AWARD TRIGGERS
    'modern award',
    'award compliance',
    'underpayment',
    'wage theft',
    'back pay',
    'penalty rates',
    'overtime',
    'casual conversion',
    'sham contracting',
    'misclassification',

    # FAIR WORK TRIGGERS
    'Fair Work Commission',
    'Fair Work Ombudsman',
    'FWC',
    'FWO',
    'enterprise agreement',
    'EBA',
    'industrial action',
    'protected action',
    'strike',
    'work ban'
]

# Specific adverse action claim triggers
ADVERSE_ACTION_TRIGGERS = [
    'fired after complaint',
    'terminated after raising concerns',
    'demoted after',
    'dismissed for',
    'sacked after',
    'stood down',
    'suspended pending investigation',
    'performance managed',
    'pushed out',
    'forced resignation'
]

# Whistleblowing specific triggers
WHISTLEBLOWING_TRIGGERS = [
    'whistleblower complaint',
    'internal disclosure',
    'reported misconduct',
    'raised concerns',
    'safety concerns',
    'fraud allegations',
    'regulatory breach',
    'cover up',
    'culture of silence',
    'speaking up'
]

# Restructure triggers indicating advisory opportunity
RESTRUCTURE_TRIGGERS = [
    'strategic review',
    'business transformation',
    'operating model',
    'cost reduction program',
    'efficiency dividend',
    'headcount reduction',
    'voluntary redundancy',
    'compulsory redundancy',
    'consultation process',
    'change management'
]

# Your firm's conflict check - companies to exclude from briefings
EXCLUDED_COMPANIES = [
    # Add ACNs or company names of existing clients to avoid conflicts
    # Example: "Client Company Pty Ltd ACN 987654321",
]

# ============================================================================
# EMPLOYMENT LAW REGULATORY SOURCES
# ============================================================================

# Fair Work sources to check daily
FAIR_WORK_SOURCES = {
    "fwc_decisions": "https://www.fwc.gov.au/decisions",
    "fwc_media": "https://www.fwc.gov.au/about-us/news-and-media",
    "fwo_media": "https://www.fairwork.gov.au/newsroom/media-releases",
    "fwo_compliance": "https://www.fairwork.gov.au/about-us/compliance-and-enforcement"
}

# ASIC sources for whistleblower and corporate governance issues
ASIC_SOURCES = {
    "published_notices": "https://publishednotices.asic.gov.au",
    "media_releases": "https://asic.gov.au/about-asic/news-centre/",
    "whistleblower": "https://asic.gov.au/about-asic/asic-investigations-and-enforcement/whistleblowing/"
}

# Court and tribunal sources for employment matters
COURT_SOURCES = {
    "federal_court": "https://www.fedcourt.gov.au",
    "federal_circuit_court": "https://www.fcfcoa.gov.au",
    "fair_work_commission": "https://www.fwc.gov.au",
    "acat": "https://www.acat.act.gov.au",
    "ncat": "https://www.ncat.nsw.gov.au",
    "vcat": "https://www.vcat.vic.gov.au",
    "qcat": "https://www.qcat.qld.gov.au"
}

# Employment law search terms for court/tribunal filings
COURT_SEARCH_TERMS = [
    'unfair dismissal',
    'general protections',
    'adverse action',
    'unlawful termination',
    'discrimination',
    'sexual harassment',
    'bullying',
    'underpayment',
    'enterprise agreement',
    'protected action'
]

# Corporate governance triggers relevant to employment
ASIC_MONITORING = [
    'whistleblower policy',
    'director resignation',
    'CEO departure',
    'culture review',
    'governance failure',
    'regulatory investigation'
]

# ============================================================================
# INDUSTRY-SPECIFIC AWARD MONITORING
# ============================================================================

# Modern Awards relevant to target industries
RELEVANT_AWARDS = [
    'General Retail Industry Award',
    'Fast Food Industry Award',
    'Building and Construction General On-site Award',
    'Nurses Award',
    'Health Professionals and Support Services Award',
    'Aged Care Award',
    'Manufacturing and Associated Industries Award',
    'Banking Finance and Insurance Award',
    'Clerks Private Sector Award'
]

# Union activity to monitor (indicates potential disputes)
UNION_MONITORING = [
    'SDA',  # Shop Distributive and Allied
    'CFMEU',  # Construction
    'ANMF',  # Nurses and Midwives
    'AMWU',  # Manufacturing
    'FSU',  # Finance Sector Union
    'HSU',  # Health Services Union
    'AWU',  # Australian Workers Union
    'TWU',  # Transport Workers Union
    'United Workers Union'
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
        url = "https://www.accc.gov.au/news-centre"
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
        # AustLII Federal Court recent decisions (use HTTPS)
        url = "https://www.austlii.edu.au/au/cases/cth/FCA/"
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


def fetch_asic_published_notices():
    """Fetch recent ASIC published notices - includes director resignations, appointments, etc."""
    try:
        url = ASIC_SOURCES["published_notices"]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        notices = []

        # Look for notice items - ASIC published notices site structure
        notice_items = soup.find_all(['article', 'div', 'tr'], limit=30)

        for item in notice_items[:30]:
            # Try to extract company name and notice type
            text = item.get_text(strip=True)

            # Look for key indicators
            if any(keyword in text.lower() for keyword in ['director', 'administrator', 'liquidator', 'receiver', 'company']):
                # Try to find links
                link_elem = item.find('a', href=True)
                link = link_elem['href'] if link_elem else ''
                if link and not link.startswith('http'):
                    link = url + link

                notices.append({
                    'title': text[:200],  # Limit length
                    'link': link,
                    'source': 'ASIC Published Notices'
                })

        return {"notices": notices, "count": len(notices)}

    except Exception as e:
        print(f"Error fetching ASIC published notices: {e}")
        return {"notices": [], "count": 0, "error": str(e)}


def search_federal_court_filings():
    """Search Federal Court for recent filings with critical keywords"""
    try:
        results = []

        # Search using Google News for Federal Court filings (more reliable than scraping)
        for term in COURT_SEARCH_TERMS[:5]:  # Limit to avoid rate limiting
            query = f'site:fedcourt.gov.au "{term}" australia'
            news_results = fetch_google_news_rss(query, max_results=3, max_age_days=7)

            for article in news_results.get('articles', []):
                results.append({
                    'title': article.get('title', ''),
                    'link': article.get('link', ''),
                    'search_term': term,
                    'court': 'Federal Court',
                    'pub_date': article.get('pub_date', ''),
                    'source': 'Federal Court Filings'
                })

            time.sleep(0.3)  # Rate limiting

        return {"filings": results, "count": len(results)}

    except Exception as e:
        print(f"Error searching Federal Court: {e}")
        return {"filings": [], "count": 0, "error": str(e)}


def search_supreme_courts():
    """Search Supreme Courts for winding up and insolvency matters"""
    try:
        results = []

        # Focus on NSW and VIC (highest volume commercial matters)
        priority_courts = [
            ("supreme_court_nsw", "NSW Supreme Court"),
            ("supreme_court_vic", "VIC Supreme Court")
        ]

        for court_key, court_name in priority_courts:
            court_url = COURT_SOURCES.get(court_key, '')

            # Search for winding up and insolvency matters
            for term in ['winding up', 'administrator appointed', 'receivership'][:2]:  # Limit searches
                query = f'site:{court_url.replace("https://", "").replace("http://", "")} "{term}"'
                news_results = fetch_google_news_rss(query, max_results=2, max_age_days=7)

                for article in news_results.get('articles', []):
                    results.append({
                        'title': article.get('title', ''),
                        'link': article.get('link', ''),
                        'search_term': term,
                        'court': court_name,
                        'pub_date': article.get('pub_date', ''),
                        'source': 'Supreme Court Filings'
                    })

                time.sleep(0.3)

        return {"filings": results, "count": len(results)}

    except Exception as e:
        print(f"Error searching Supreme Courts: {e}")
        return {"filings": [], "count": 0, "error": str(e)}


def search_watchlist_in_courts():
    """Search for watchlist companies in court filings"""
    try:
        results = []

        # Search for top 10 priority watchlist companies in courts
        priority_companies = WATCHLIST_COMPANIES[:10]

        for company in priority_companies:
            # Search across court sites
            query = f'"{company}" (court OR federal court OR supreme court) australia'
            news_results = fetch_google_news_rss(query, max_results=2, max_age_days=7)

            for article in news_results.get('articles', []):
                results.append({
                    'title': article.get('title', ''),
                    'link': article.get('link', ''),
                    'company': company,
                    'pub_date': article.get('pub_date', ''),
                    'source': 'Court Filings - Watchlist'
                })

            time.sleep(0.3)

        return {"filings": results, "count": len(results)}

    except Exception as e:
        print(f"Error searching watchlist in courts: {e}")
        return {"filings": [], "count": 0, "error": str(e)}


def search_ppsr_indicators():
    """Search for PPSR-related news indicating refinancing or receiverships"""
    try:
        results = []

        # Search for PPSR activity that indicates financial distress
        queries = [
            'PPSR security interest registered australia',
            'receiver appointed PPSR australia',
            'secured creditor appointment australia'
        ]

        for query in queries:
            news_results = fetch_google_news_rss(query, max_results=3, max_age_days=7)

            for article in news_results.get('articles', []):
                results.append({
                    'title': article.get('title', ''),
                    'link': article.get('link', ''),
                    'pub_date': article.get('pub_date', ''),
                    'source': 'PPSR Indicators'
                })

            time.sleep(0.3)

        return {"articles": results, "count": len(results)}

    except Exception as e:
        print(f"Error searching PPSR indicators: {e}")
        return {"articles": [], "count": 0, "error": str(e)}


def fetch_google_news_rss(query, max_results=10, max_age_days=7, time_range='7d'):
    """Fetch news from Google News RSS feed with STRICT date filtering

    Args:
        query: Search query
        max_results: Maximum number of results to return
        max_age_days: Maximum age of articles in days (for post-filtering)
        time_range: Google News time range parameter: '1h', '1d', '7d', '1m'
    """
    try:
        # Calculate the absolute cutoff date
        now = datetime.now(datetime.now().astimezone().tzinfo)
        cutoff_datetime = now - timedelta(days=max_age_days)
        date_str = cutoff_datetime.strftime('%Y-%m-%d')

        # Use 'after:' parameter which Google News respects better than 'when:'
        time_filtered_query = f"{query} after:{date_str}"

        # Google News RSS URL with Australian localization
        rss_url = f"https://news.google.com/rss/search?q={time_filtered_query.replace(' ', '+')}&hl=en-AU&gl=AU&ceid=AU:en"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Retry logic for transient SSL/connection errors
        max_retries = 3
        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.get(rss_url, headers=headers, timeout=15)
                response.raise_for_status()
                break
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff: 1s, 2s
                    continue
                else:
                    raise last_error

        # Parse XML RSS feed
        soup = BeautifulSoup(response.content, 'xml')
        articles = []

        # Find all item elements (fetch more to account for filtering)
        items = soup.find_all('item', limit=max_results * 3)

        skipped_old = 0
        skipped_no_date = 0

        for item in items:
            title_elem = item.find('title')
            pubdate_elem = item.find('pubDate')
            link_elem = item.find('link')

            # CRITICAL: Must have both title and date
            if not title_elem or not pubdate_elem:
                skipped_no_date += 1
                continue

            try:
                # CRITICAL: Parse and validate the publication date
                pub_datetime = parsedate_to_datetime(pubdate_elem.get_text(strip=True))

                # Calculate precise age
                age_seconds = (now - pub_datetime).total_seconds()
                age_hours = age_seconds / 3600
                age_days = age_seconds / 86400  # Use precise days calculation

                # STRICT CUTOFF: Reject anything older than max_age_days
                if age_days > max_age_days:
                    skipped_old += 1
                    continue

                # Additional safety check: reject articles from before 2026
                if pub_datetime.year < 2026:
                    skipped_old += 1
                    continue

                # Categorize by age
                if age_hours <= 24:
                    time_category = '24h'
                elif age_days <= 7:
                    time_category = '7d'
                else:
                    time_category = 'old'

                articles.append({
                    'title': title_elem.get_text(strip=True),
                    'source': 'Google News',
                    'published': pubdate_elem.get_text(strip=True),
                    'link': link_elem.get_text(strip=True) if link_elem else '',
                    'age_days': round(age_days, 2),
                    'age_hours': round(age_hours, 1),
                    'time_category': time_category,
                    'pub_date': pub_datetime.strftime('%Y-%m-%d %H:%M'),
                    'pub_datetime': pub_datetime
                })

            except Exception as e:
                # If date parsing fails, skip the article completely
                skipped_no_date += 1
                continue

        # Sort by age (newest first) and limit to max_results
        articles.sort(key=lambda x: x.get('age_hours', 9999))
        articles = articles[:max_results]

        # Debug info
        if skipped_old > 0 or skipped_no_date > 0:
            print(f"    [{query[:30]}...] Filtered: {skipped_old} old, {skipped_no_date} no date")

        return {"articles": articles, "count": len(articles)}

    except Exception as e:
        print(f"Error fetching Google News for '{query}': {e}")
        return {"articles": [], "count": 0, "error": str(e)}


def search_watchlist_companies():
    """Search for employment law triggers at ALL watchlist companies"""
    company_news = []

    print(f"  Searching for all {len(WATCHLIST_COMPANIES)} watchlist companies (employment law triggers)...")

    for i, company in enumerate(WATCHLIST_COMPANIES, 1):
        if company:
            try:
                # EMPLOYMENT LAW FOCUSED: Search strategies for adverse action triggers
                queries = [
                    # Strategy 1: Restructure and redundancy triggers
                    f'{company} redundancy',
                    f'{company} restructure',
                    f'{company} job cuts',
                    f'{company} layoffs',

                    # Strategy 2: Workplace issues and disputes
                    f'{company} workplace',
                    f'{company} employees',
                    f'{company} staff',
                    f'{company} workers',

                    # Strategy 3: Adverse action and whistleblowing
                    f'{company} whistleblower',
                    f'{company} fired',
                    f'{company} dismissed',
                    f'{company} Fair Work',

                    # Strategy 4: Award and underpayment
                    f'{company} underpayment',
                    f'{company} wages',
                    f'{company} back pay',
                ]

                company_articles = []
                for query in queries:
                    # Get latest news (7 days) for each query
                    results = fetch_google_news_rss(query, max_results=3, max_age_days=7, time_range='7d')
                    company_articles.extend(results.get('articles', []))
                    time.sleep(0.2)  # Faster rate between queries for same company

                # Deduplicate by title
                seen_titles = set()
                unique_articles = []
                for article in company_articles:
                    title = article.get('title', '')
                    # Only include if company name actually appears in title (relevance check)
                    if title and title not in seen_titles and company.lower() in title.lower():
                        seen_titles.add(title)
                        unique_articles.append(article)

                if len(unique_articles) > 0:
                    # Show age breakdown
                    age_24h = sum(1 for a in unique_articles if a.get('time_category') == '24h')
                    age_7d = sum(1 for a in unique_articles if a.get('time_category') == '7d')

                    print(f"    [{i}/{len(WATCHLIST_COMPANIES)}] {company}: {len(unique_articles)} articles (24h:{age_24h} 7d:{age_7d})")
                    company_news.extend(unique_articles[:10])  # Top 10 per company
                else:
                    print(f"    [{i}/{len(WATCHLIST_COMPANIES)}] {company}: No news (last 7 days)")

                time.sleep(0.3)  # Rate limiting between companies

            except Exception as e:
                print(f"    Error searching for {company}: {e}")
                continue

    return {"articles": company_news, "count": len(company_news)}


def load_seen_articles():
    """Load previously seen article titles to avoid repeating old news"""
    seen_file = 'seen_articles.json'
    try:
        if os.path.exists(seen_file):
            with open(seen_file, 'r') as f:
                data = json.load(f)
                # Clean out entries older than 14 days
                cutoff = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
                return {k: v for k, v in data.items() if v >= cutoff}
        return {}
    except:
        return {}


def save_seen_articles(seen_articles):
    """Save seen article titles with date"""
    seen_file = 'seen_articles.json'
    try:
        with open(seen_file, 'w') as f:
            json.dump(seen_articles, f)
    except Exception as e:
        print(f"Warning: Could not save seen articles: {e}")


def fetch_australian_legal_news():
    """Aggregate Australian employment law news - focusing on adverse action triggers"""
    all_news = []

    # Load previously seen articles to avoid duplicates
    seen_articles = load_seen_articles()
    print(f"  Loaded {len(seen_articles)} previously seen articles (last 14 days)")

    # ========================================================================
    # ADVERSE ACTION & GENERAL PROTECTIONS TRIGGERS
    # ========================================================================

    print("  - Adverse action & general protections (7d)...")
    adverse_action = fetch_google_news_rss("australia adverse action unfair dismissal general protections", max_results=15, max_age_days=7, time_range='7d')
    all_news.extend(adverse_action.get('articles', []))
    time.sleep(0.5)

    print("  - Unlawful termination claims (7d)...")
    termination = fetch_google_news_rss("australia unlawful termination wrongful dismissal sacked fired", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(termination.get('articles', []))
    time.sleep(0.5)

    print("  - Workplace discrimination & harassment (7d)...")
    discrimination = fetch_google_news_rss("australia workplace discrimination harassment bullying", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(discrimination.get('articles', []))
    time.sleep(0.5)

    # ========================================================================
    # WHISTLEBLOWING TRIGGERS
    # ========================================================================

    print("  - Whistleblower news (7d)...")
    whistleblower = fetch_google_news_rss("australia whistleblower disclosure retaliation", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(whistleblower.get('articles', []))
    time.sleep(0.5)

    print("  - Corporate misconduct & cover-ups (7d)...")
    misconduct = fetch_google_news_rss("australia corporate misconduct cover up scandal exposed", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(misconduct.get('articles', []))
    time.sleep(0.5)

    print("  - Safety concerns raised (7d)...")
    safety = fetch_google_news_rss("australia workplace safety concerns raised reported", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(safety.get('articles', []))
    time.sleep(0.5)

    # ========================================================================
    # RESTRUCTURE & REDUNDANCY TRIGGERS
    # ========================================================================

    print("  - Restructures & job cuts (7d)...")
    restructure = fetch_google_news_rss("australia restructure redundancy job cuts layoffs", max_results=15, max_age_days=7, time_range='7d')
    all_news.extend(restructure.get('articles', []))
    time.sleep(0.5)

    print("  - Workforce reduction announcements (7d)...")
    workforce = fetch_google_news_rss("australia workforce reduction downsizing headcount cuts", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(workforce.get('articles', []))
    time.sleep(0.5)

    print("  - Company transformation & efficiency (7d)...")
    transformation = fetch_google_news_rss("australia business transformation efficiency review cost cutting", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(transformation.get('articles', []))
    time.sleep(0.5)

    # ========================================================================
    # MODERN AWARDS & UNDERPAYMENT TRIGGERS
    # ========================================================================

    print("  - Wage theft & underpayment (7d)...")
    underpayment = fetch_google_news_rss("australia underpayment wage theft back pay penalty rates", max_results=15, max_age_days=7, time_range='7d')
    all_news.extend(underpayment.get('articles', []))
    time.sleep(0.5)

    print("  - Award compliance issues (7d)...")
    award = fetch_google_news_rss("australia modern award compliance breach enterprise agreement", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(award.get('articles', []))
    time.sleep(0.5)

    print("  - Casual conversion & sham contracting (7d)...")
    casual = fetch_google_news_rss("australia casual conversion sham contracting misclassification gig economy", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(casual.get('articles', []))
    time.sleep(0.5)

    # ========================================================================
    # FAIR WORK COMMISSION & REGULATORY
    # ========================================================================

    print("  - Fair Work Commission decisions (7d)...")
    fwc = fetch_google_news_rss("australia Fair Work Commission decision ruling", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(fwc.get('articles', []))
    time.sleep(0.5)

    print("  - Fair Work Ombudsman enforcement (7d)...")
    fwo = fetch_google_news_rss("australia Fair Work Ombudsman enforcement prosecution penalty", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(fwo.get('articles', []))
    time.sleep(0.5)

    # ========================================================================
    # INDUSTRIAL ACTION & UNION ACTIVITY
    # ========================================================================

    print("  - Industrial action & strikes (7d)...")
    industrial = fetch_google_news_rss("australia strike industrial action protected action work ban", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(industrial.get('articles', []))
    time.sleep(0.5)

    print("  - Union disputes (7d)...")
    union = fetch_google_news_rss("australia union dispute enterprise bargaining agreement", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(union.get('articles', []))
    time.sleep(0.5)

    # ========================================================================
    # TARGET INDUSTRIES - SPECIFIC SEARCHES
    # ========================================================================

    # RETAIL
    print("  - Retail sector employment news (7d)...")
    retail = fetch_google_news_rss("australia retail workers staff redundancy underpayment Woolworths Coles", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(retail.get('articles', []))
    time.sleep(0.5)

    # CONSTRUCTION
    print("  - Construction sector employment news (7d)...")
    construction = fetch_google_news_rss("australia construction workers safety dispute CFMEU redundancy", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(construction.get('articles', []))
    time.sleep(0.5)

    # HEALTHCARE
    print("  - Healthcare sector employment news (7d)...")
    healthcare = fetch_google_news_rss("australia healthcare nurses staff shortage aged care hospital workers", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(healthcare.get('articles', []))
    time.sleep(0.5)

    # MANUFACTURING
    print("  - Manufacturing sector employment news (7d)...")
    manufacturing = fetch_google_news_rss("australia manufacturing workers factory closure redundancy", max_results=10, max_age_days=7, time_range='7d')
    all_news.extend(manufacturing.get('articles', []))
    time.sleep(0.5)

    # FINANCIAL SERVICES
    print("  - Financial services employment news (7d)...")
    finance = fetch_google_news_rss("australia bank insurance financial services redundancy restructure whistleblower", max_results=12, max_age_days=7, time_range='7d')
    all_news.extend(finance.get('articles', []))
    time.sleep(0.5)

    # ========================================================================
    # WATCHLIST COMPANIES - Employment Law Focus
    # ========================================================================

    print(f"  - Watchlist company employment triggers ({len(WATCHLIST_COMPANIES)} companies, 7d)...")
    watchlist_results = search_watchlist_companies()
    all_news.extend(watchlist_results.get('articles', []))

    print(f"\n  Total articles collected: {len(all_news)}")

    # Deduplicate all articles by title AND filter out previously seen articles
    today = datetime.now().strftime('%Y-%m-%d')
    seen_titles = set()
    unique_all_news = []
    new_articles_count = 0

    for article in all_news:
        title = article.get('title', '')
        if title and title not in seen_titles:
            # Check if we've seen this article before (in last 14 days)
            if title in seen_articles:
                # Skip articles we've already reported
                continue

            seen_titles.add(title)
            unique_all_news.append(article)

            # Mark as seen with today's date
            seen_articles[title] = today
            new_articles_count += 1

    # Save updated seen articles list
    save_seen_articles(seen_articles)

    print(f"  After deduplication: {len(unique_all_news)} unique articles")
    print(f"  New articles (never seen before): {new_articles_count}")
    print(f"  Total seen articles tracked: {len(seen_articles)}")

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

    # NEW ENHANCED SOURCES - More up-to-date intelligence
    print("- Fetching ASIC published notices (director changes, appointments)...")
    asic_notices = fetch_asic_published_notices()

    print("- Searching Federal Court filings (winding up, statutory demands)...")
    federal_court = search_federal_court_filings()

    print("- Searching Supreme Court filings (NSW/VIC insolvency matters)...")
    supreme_court = search_supreme_courts()

    print("- Searching for watchlist companies in court filings...")
    watchlist_courts = search_watchlist_in_courts()

    print("- Searching PPSR indicators (refinancing, receiver appointments)...")
    ppsr_data = search_ppsr_indicators()

    # Prepare data summary for Claude
    watchlist_str = "\n".join([f"- {company}" for company in WATCHLIST_COMPANIES if company])
    industries_str = ", ".join(PRIORITY_INDUSTRIES)
    keywords_str = ", ".join(HIGH_VALUE_KEYWORDS)

    # Debug: Print data collection results
    print(f"\nData Collection Summary:")
    print(f"  ASIC releases: {asic_data.get('count', 0)}")
    print(f"  ASIC published notices: {asic_notices.get('count', 0)}")
    print(f"  ACCC releases: {accc_data.get('count', 0)}")
    print(f"  AustLII cases: {austlii_data.get('count', 0)}")
    print(f"  Federal Court filings: {federal_court.get('count', 0)}")
    print(f"  Supreme Court filings: {supreme_court.get('count', 0)}")
    print(f"  Watchlist in courts: {watchlist_courts.get('count', 0)}")
    print(f"  PPSR indicators: {ppsr_data.get('count', 0)}")
    print(f"  News articles: {news_data.get('count', 0)}")
    total_points = (asic_data.get('count', 0) + asic_notices.get('count', 0) + accc_data.get('count', 0) +
                   austlii_data.get('count', 0) + federal_court.get('count', 0) + supreme_court.get('count', 0) +
                   watchlist_courts.get('count', 0) + ppsr_data.get('count', 0) + news_data.get('count', 0))
    print(f"  Total data points: {total_points}\n")

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

    # Show publication dates to verify recency - INCLUDE LINKS for reference section
    news_articles_str = "LAST 24 HOURS (IMMEDIATE OPPORTUNITIES):\n"
    news_articles_str += "\n".join([
        f"- [{a.get('pub_date', 'Unknown date')}] {a.get('title', 'No title')}\n  Link: {a.get('link', 'No link')}"
        for a in articles_24h[:30]
    ]) or "No articles in last 24 hours\n"

    news_articles_str += "\n\nLAST 2-7 DAYS (RECENT DEVELOPMENTS):\n"
    news_articles_str += "\n".join([
        f"- [{a.get('pub_date', 'Unknown date')}] {a.get('title', 'No title')}\n  Link: {a.get('link', 'No link')}"
        for a in articles_7d[:30]
    ]) or "No articles from 2-7 days ago"

    # Format NEW ENHANCED SOURCES
    # ASIC Published Notices
    asic_notices_str = "\n".join([
        f"- {n.get('title', 'No title')}\n  Link: {n.get('link', 'No link')}"
        for n in asic_notices.get('notices', [])[:15]
    ]) or "No recent ASIC published notices found"

    # Federal Court Filings
    federal_court_str = "\n".join([
        f"- [{f.get('pub_date', 'Recent')}] {f.get('title', 'No title')} (Search: {f.get('search_term', '')})\n  Link: {f.get('link', 'No link')}"
        for f in federal_court.get('filings', [])[:15]
    ]) or "No recent Federal Court filings found"

    # Supreme Court Filings
    supreme_court_str = "\n".join([
        f"- [{s.get('pub_date', 'Recent')}] {s.get('title', 'No title')} ({s.get('court', '')})\n  Link: {s.get('link', 'No link')}"
        for s in supreme_court.get('filings', [])[:15]
    ]) or "No recent Supreme Court filings found"

    # Watchlist in Courts
    watchlist_courts_str = "\n".join([
        f"- [{w.get('pub_date', 'Recent')}] {w.get('title', 'No title')} (Company: {w.get('company', '')})\n  Link: {w.get('link', 'No link')}"
        for w in watchlist_courts.get('filings', [])[:15]
    ]) or "No watchlist companies found in court filings"

    # PPSR Indicators
    ppsr_str = "\n".join([
        f"- [{p.get('pub_date', 'Recent')}] {p.get('title', 'No title')}\n  Link: {p.get('link', 'No link')}"
        for p in ppsr_data.get('articles', [])[:10]
    ]) or "No recent PPSR indicators found"

    # Format employment law trigger keywords for the prompt
    adverse_triggers_str = ", ".join(ADVERSE_ACTION_TRIGGERS[:10])
    whistleblowing_triggers_str = ", ".join(WHISTLEBLOWING_TRIGGERS[:10])
    restructure_triggers_str = ", ".join(RESTRUCTURE_TRIGGERS[:10])

    data_summary = f"""
EMPLOYMENT LAW INTELLIGENCE - DATA COLLECTED FROM AUSTRALIAN SOURCES:

=== SERVICE FOCUS ===
We are offering PROACTIVE EMPLOYMENT LAW ADVISORY SERVICES on:
1. ADVERSE ACTION CLAIMS - general protections, unlawful termination, discrimination
2. WHISTLEBLOWING - protected disclosures, retaliation, public interest disclosures
3. RESTRUCTURES - redundancy consultation, change management, workforce reduction
4. MODERN AWARDS - award compliance, underpayment, casual conversion, sham contracting

=== TARGET INDUSTRIES ===
Priority: Retail, Construction, Healthcare, Manufacturing, Financial Services

=== REGULATORY SOURCES ===

Fair Work & ASIC Releases ({asic_data.get('count', 0)} items):
{asic_releases_str}

ASIC Published Notices ({asic_notices.get('count', 0)} notices) - CORPORATE GOVERNANCE, WHISTLEBLOWER POLICIES:
{asic_notices_str}

ACCC Announcements ({accc_data.get('count', 0)} items):
{accc_releases_str}

=== EMPLOYMENT TRIBUNAL & COURT FILINGS ===

Federal Court/FWC Filings ({federal_court.get('count', 0)} filings) - UNFAIR DISMISSAL, ADVERSE ACTION:
{federal_court_str}

State Tribunal Filings ({supreme_court.get('count', 0)} filings) - DISCRIMINATION, HARASSMENT:
{supreme_court_str}

Watchlist Companies in Employment Matters ({watchlist_courts.get('count', 0)} mentions):
{watchlist_courts_str}

Recent Employment Cases from AustLII ({austlii_data.get('count', 0)} cases):
{austlii_cases_str}

=== EMPLOYMENT LAW NEWS & TRIGGERS ===

Employment Law News ({news_data.get('count', 0)} articles):
{news_articles_str}

=== TRIGGER KEYWORDS TO WATCH ===

Adverse Action Triggers: {adverse_triggers_str}
Whistleblowing Triggers: {whistleblowing_triggers_str}
Restructure Triggers: {restructure_triggers_str}

=== MONITORING PRIORITIES ===
Watchlist Companies ({len([c for c in WATCHLIST_COMPANIES if c.strip()])} major employers):
{watchlist_str}

Target Industries: {industries_str}
High-Value Keywords: {keywords_str}
    """

    # Call Claude to analyze and generate briefing
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": f"""You are an employment law intelligence analyst for a top-tier Australian employment law firm.

We are proactively offering EMPLOYMENT LAW ADVISORY SERVICES focused on:
1. **ADVERSE ACTION CLAIMS** - general protections, unlawful termination, discrimination, harassment
2. **WHISTLEBLOWING** - protected disclosures, retaliation claims, public interest disclosures
3. **RESTRUCTURES** - redundancy consultation, change management, workforce reduction planning
4. **MODERN AWARDS** - award compliance audits, underpayment remediation, casual conversion

TARGET INDUSTRIES: Retail, Construction, Healthcare, Manufacturing, Financial Services

Analyze this data from {datetime.now().strftime('%B %d, %Y')} (Australian sources):

{data_summary}

CRITICAL INSTRUCTIONS - IDENTIFY ADVISORY OPPORTUNITIES:
- Look for TRIGGER SIGNS where companies need proactive employment law advice
- Focus on companies BEFORE they get into trouble (advisory, not litigation)
- Identify restructures, redundancies, workforce changes = need consultation advice
- Spot whistleblower situations early = need policy review and response advice
- Find underpayment news = need audit and remediation advice
- Watch for workplace culture issues = need training and policy advice

EMPLOYMENT LAW FEE ESTIMATION GUIDELINES:
Use these rates for fee estimates:
- Partners: AUD $800-1,000/hour
- Special Counsel: AUD $600-700/hour
- Senior Associate: AUD $500-600/hour
- Associate: AUD $350-450/hour

Typical matter values:
- Restructure/Redundancy Advisory: $50,000 - $250,000 (depending on workforce size)
- Award Compliance Audit: $30,000 - $150,000
- Whistleblower Response: $75,000 - $300,000
- Adverse Action Defence: $100,000 - $500,000+
- Enterprise Agreement Negotiation: $150,000 - $500,000+

Generate a comprehensive employment law intelligence briefing with:

## Executive Summary
Provide 2-3 sentences highlighting the most significant EMPLOYMENT LAW triggers from the last 7 days.
Focus on proactive advisory opportunities, not just litigation.

## High-Priority Advisory Opportunities

Identify companies that need PROACTIVE employment law advice based on:

### RESTRUCTURE & REDUNDANCY OPPORTUNITIES
Companies announcing or considering:
- Job cuts, layoffs, redundancies
- Business transformation, efficiency reviews
- Cost cutting, workforce reduction
- Site closures, business unit changes

For each, identify the ADVISORY opportunity:
- Redundancy consultation process design
- Selection criteria development
- Communication strategy
- Redeployment programs
- Enterprise agreement implications

### WHISTLEBLOWER ADVISORY OPPORTUNITIES
Companies experiencing:
- Whistleblower complaints (public or rumoured)
- Corporate misconduct allegations
- Safety concerns raised
- Regulatory investigations
- Culture issues exposed

Advisory opportunity:
- Whistleblower policy review
- Investigation protocols
- Response strategy
- Board reporting
- Retaliation prevention

### AWARD COMPLIANCE OPPORTUNITIES
Companies with:
- Underpayment discoveries
- Wage theft allegations
- Award interpretation disputes
- Casual workforce issues
- Contractor vs employee disputes

Advisory opportunity:
- Payroll audit
- Remediation program design
- Self-disclosure to FWO
- Award classification review
- Casual conversion compliance

### ADVERSE ACTION PREVENTION
Companies showing signs of:
- Difficult terminations coming
- Performance management programs
- Discrimination allegations
- Harassment claims
- Union disputes

Advisory opportunity:
- Termination process design
- Performance management frameworks
- Investigation training
- Policy review and update
- Union negotiation support

For EACH opportunity, include:

### [Company Name] - [Opportunity Type]
**Trigger Event**: What happened that creates the opportunity?

**Advisory Services Needed**:
- [List specific services we can offer]

**Estimated Fees**:
- Fee Range: $XX,XXX - $XXX,XXX
- Scope: [Brief scope description]

**Why Now? (Timing Analysis)**:
- What makes this urgent?
- Window of opportunity?
- Competitive timing factors?

**Industry Context**:
- Industry: [Retail/Construction/Healthcare/Manufacturing/Financial Services]
- Workforce size estimate: [if known]
- Award coverage: [relevant modern awards]

**Priority Score**: [High/Medium/Low]
- Likelihood of needing advice: [1-10]
- Fee potential: [1-10]
- Timing urgency: [1-10]

**Source Links**: [List sources]

---

## Watchlist Company Alerts

Specifically flag ANY employment law triggers at our {len(WATCHLIST_COMPANIES)} watchlist companies:
{watchlist_str}

Even minor workforce news is valuable - restructures, new hires, departures, workplace incidents.

## Industry-Specific Opportunities

### Retail Sector
- Award compliance issues (General Retail Industry Award)
- Casual conversion obligations
- Underpayment remediation
- Restructure/store closure advice

### Construction Sector
- CFMEU/union activity
- Safety whistleblowing
- Subcontractor vs employee issues
- Project wind-down redundancies

### Healthcare Sector
- Nurse/staff shortages creating pressure
- Aged care compliance
- Bullying and harassment
- Whistleblower protections

### Manufacturing Sector
- Factory closures
- Automation/redundancy programs
- Award modernisation
- Overseas relocation advice

### Financial Services Sector
- Post-Royal Commission culture issues
- Whistleblower protections
- Restructures and redundancies
- Conduct and compliance training

## Emerging Trends
What patterns do you see that suggest future advisory opportunities?
- Regulatory focus areas (FWO priorities)
- Industry-wide issues
- Legislative changes coming
- Economic pressures driving workforce changes

## Top 10 Action Items
Rank by ADVISORY opportunity (not litigation):
1. [Highest priority - Company + Opportunity + Rationale]
2. [Second priority]
...

Focus on:
- Companies to approach proactively
- Industries showing systemic issues
- Regulatory developments creating advisory demand
- Upcoming compliance deadlines

## References
List ALL source links grouped by topic:
- Restructure/Redundancy news
- Whistleblower news
- Underpayment/Award news
- Workplace culture news
- Fair Work/Regulatory news

Be direct and practical - this briefing drives proactive business development for employment law advisory services."""
        }]
    )

    return message.content[0].text


def format_briefing_html(briefing_content):
    """Convert briefing markdown to beautifully formatted HTML"""
    # Escape HTML special characters first
    content = briefing_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # Convert markdown headings to styled HTML
    # ## Heading -> <h2>
    content = re.sub(r'^## (.+)$', r'<h2 style="text-decoration: underline; color: #1a1a1a; margin-top: 25px; margin-bottom: 15px; font-size: 14pt; font-weight: bold;">\1</h2>', content, flags=re.MULTILINE)

    # ### Sub-heading -> <h3>
    content = re.sub(r'^### (.+)$', r'<h3 style="text-decoration: underline; color: #2c3e50; margin-top: 20px; margin-bottom: 10px; font-size: 11pt; font-weight: bold;">\1</h3>', content, flags=re.MULTILINE)

    # Bold **text** or company names in ALL CAPS
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)

    # Bold section labels (e.g., "Overview:", "Estimated Legal Fees:")
    content = re.sub(r'^(\w[\w\s&]+?):', r'<strong>\1:</strong>', content, flags=re.MULTILINE)

    # Bold company names (watchlist companies)
    for company in WATCHLIST_COMPANIES:
        if company:
            # Bold the company name wherever it appears
            content = re.sub(rf'\b({re.escape(company)})\b', r'<strong>\1</strong>', content, flags=re.IGNORECASE)

    # Convert bullet points
    content = re.sub(r'^- (.+)$', r'<li style="margin-bottom: 8px;">\1</li>', content, flags=re.MULTILINE)

    # Wrap consecutive <li> items in <ul>
    content = re.sub(r'(<li.+?</li>)(\n<li.+?</li>)+', lambda m: '<ul style="margin-left: 20px; margin-bottom: 15px;">' + m.group(0) + '</ul>', content, flags=re.DOTALL)

    # Convert links to clickable links
    content = re.sub(r'(https?://[^\s<]+)', r'<a href="\1" style="color: #0066cc; text-decoration: none;">\1</a>', content)

    # Add line breaks for better spacing
    content = content.replace('\n\n', '<br><br>')
    content = content.replace('\n', '<br>')

    # Highlight priority indicators
    content = re.sub(r'\b(HIGH|URGENT|IMMEDIATE)\b', r'<span style="background-color: #fff3cd; padding: 2px 6px; border-radius: 3px; font-weight: bold;">\1</span>', content, flags=re.IGNORECASE)
    content = re.sub(r'\b(OVERALL PRIORITY: High)\b', r'<span style="background-color: #ffebee; color: #c62828; padding: 2px 6px; border-radius: 3px; font-weight: bold;">\1</span>', content, flags=re.IGNORECASE)

    return content


def save_briefing(briefing_content):
    """Save briefing to file"""
    timestamp = datetime.now().strftime('%Y-%m-%d')
    filename = f'briefing_{timestamp}.txt'

    with open(filename, 'w') as f:
        f.write(f"Employment Law Intelligence Briefing - {timestamp}\n")
        f.write("Focus: Adverse Action | Whistleblowing | Restructures | Modern Awards\n")
        f.write("Industries: Retail | Construction | Healthcare | Manufacturing | Financial Services\n")
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
        msg['Subject'] = f"Employment Law Advisory Opportunities - {datetime.now().strftime('%B %d, %Y')}"
        msg['From'] = email_from
        msg['To'] = email_to

        # Plain text version
        text_content = briefing_content

        # HTML version with professional formatting
        formatted_content = format_briefing_html(briefing_content)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.6;
            color: #333;
            background-color: #f9f9f9;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 30px;
            border: 1px solid #ddd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            background-color: #1a1a1a;
            color: #ffffff;
            padding: 20px;
            margin: -30px -30px 30px -30px;
            border-bottom: 4px solid #0066cc;
        }}
        .header h1 {{
            margin: 0;
            font-size: 16pt;
            font-weight: bold;
        }}
        .header .date {{
            margin: 5px 0 0 0;
            font-size: 9pt;
            color: #cccccc;
        }}
        h2 {{
            color: #1a1a1a;
            text-decoration: underline;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 14pt;
            font-weight: bold;
        }}
        h3 {{
            color: #2c3e50;
            text-decoration: underline;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 11pt;
            font-weight: bold;
        }}
        strong {{
            font-weight: bold;
            color: #1a1a1a;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul {{
            margin-left: 20px;
            margin-bottom: 15px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            font-size: 8pt;
            color: #666;
            text-align: center;
        }}
        .priority-high {{
            background-color: #ffebee;
            color: #c62828;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .priority-medium {{
            background-color: #fff3e0;
            color: #ef6c00;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Employment Law Advisory Opportunities</h1>
            <div class="date">Generated: {datetime.now().strftime('%B %d, %Y at %H:%M AEST')}</div>
            <div class="date">Focus: Adverse Action | Whistleblowing | Restructures | Modern Awards</div>
        </div>
        <div class="content">
            {formatted_content}
        </div>
        <div class="footer">
            <p><strong>Employment Law Intelligence Briefing</strong> - Automated Daily Report</p>
            <p>Monitoring {len([c for c in WATCHLIST_COMPANIES if c.strip()])} major employers across {len(PRIORITY_INDUSTRIES)} target industries</p>
            <p>Industries: Retail | Construction | Healthcare | Manufacturing | Financial Services</p>
            <p>Sources: Fair Work Commission, Fair Work Ombudsman, ASIC, News Media</p>
        </div>
    </div>
</body>
</html>"""

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
    print("=" * 70)
    print("EMPLOYMENT LAW INTELLIGENCE BRIEFING")
    print("=" * 70)
    print(f"Focus: Adverse Action | Whistleblowing | Restructures | Modern Awards")
    print(f"Industries: {', '.join(PRIORITY_INDUSTRIES)}")
    print(f"Monitoring {len([c for c in WATCHLIST_COMPANIES if c.strip()])} major employers")
    print("=" * 70)

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
