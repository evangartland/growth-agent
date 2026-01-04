import anthropic
import requests
from datetime import datetime, timedelta
import os
import json
from bs4 import BeautifulSoup
import time
import re

def fetch_asic_insolvency_notices():
    """
    Fetch recent ASIC insolvency notices from the public website
    """
    notices = []
    try:
        # ASIC publishes insolvency notices publicly
        url = "https://insolvencynotices.asic.gov.au/browsesearch-notices/notice-search"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Try to get the main page first
        response = requests.get("https://insolvencynotices.asic.gov.au/browsesearch-notices/", 
                              headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for recent notices on the page
            # ASIC's structure may vary, so we'll look for common patterns
            notice_links = soup.find_all('a', href=re.compile(r'/browsesearch-notices/'))[:15]
            
            for link in notice_links:
                text = link.get_text(strip=True)
                if text and len(text) > 10:  # Filter out empty/short links
                    notices.append({
                        'text': text[:200],  # Limit length
                        'link': link.get('href', ''),
                        'source': 'ASIC Insolvency Notices'
                    })
            
            # If we found notices, great. If not, we'll note it.
            if notices:
                print(f"✓ Found {len(notices)} ASIC insolvency notice references")
            else:
                print("⚠ No specific notices found - may need to configure search parameters")
                notices = [{
                    'note': 'ASIC Insolvency Notices page accessed but no specific notices parsed',
                    'action': 'Visit https://insolvencynotices.asic.gov.au/ for manual review',
                    'status': 'Requires search parameter configuration'
                }]
        else:
            notices = [{
                'error': f'HTTP {response.status_code}',
                'note': 'Could not access ASIC Insolvency Notices',
                'url': 'https://insolvencynotices.asic.gov.au/'
            }]
            
    except Exception as e:
        print(f"✗ Error fetching ASIC insolvency notices: {str(e)}")
        notices = [{
            'error': str(e)[:200],
            'source': 'ASIC Insolvency Notices',
            'fallback': 'Manual monitoring required'
        }]
    
    return notices

def fetch_asic_company_announcements():
    """
    Fetch ASIC media releases and company announcements
    """
    announcements = []
    
    try:
        url = "https://asic.gov.au/about-asic/news-centre/find-a-media-release/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find media releases
            articles = soup.find_all(['article', 'div'], class_=re.compile(r'media|release|news'), limit=10)
            
            if not articles:
                # Try alternative selectors
                articles = soup.find_all('a', href=re.compile(r'/media-release/|/news/'))[:10]
            
            for article in articles:
                title_elem = article.find(['h2', 'h3', 'h4', 'a'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 15:  # Filter out navigation items
                        announcements.append({
                            'title': title[:250],
                            'source': 'ASIC Media Release'
                        })
            
            if announcements:
                print(f"✓ Found {len(announcements)} ASIC media releases")
            else:
                print("⚠ ASIC media releases page structure may have changed")
                announcements = [{
                    'note': 'ASIC media releases require updated parsing',
                    'url': url
                }]
        
    except Exception as e:
        print(f"✗ Error fetching ASIC announcements: {str(e)}")
        announcements = [{
            'error': str(e)[:200],
            'source': 'ASIC'
        }]
    
    return announcements

def fetch_federal_court_notices():
    """
    Fetch Federal Court of Australia recent cases and notices
    """
    filings = []
    
    try:
        # Try the Federal Court's case law search
        url = "https://www.fedcourt.gov.au/digital-law-library/judgments/search"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for recent judgments
            case_links = soup.find_all('a', href=re.compile(r'/judgment/'))[:10]
            
            for link in case_links:
                case_title = link.get_text(strip=True)
                if len(case_title) > 10:
                    filings.append({
                        'case': case_title[:300],
                        'url': link.get('href', ''),
                        'source': 'Federal Court'
                    })
            
            if filings:
                print(f"✓ Found {len(filings)} Federal Court cases")
            else:
                filings = [{
                    'note': 'Federal Court search accessible, configure for specific practice areas',
                    'url': url,
                    'suggestion': 'Filter by: Corporations, Insolvency, Administrative Law'
                }]
        
    except Exception as e:
        print(f"✗ Error fetching Federal Court data: {str(e)}")
        filings = [{
            'error': str(e)[:200],
            'source': 'Federal Court'
        }]
    
    return filings

def fetch_accc_enforcement():
    """
    Monitor ACCC enforcement actions and media releases
    """
    enforcement = []
    
    try:
        url = "https://www.accc.gov.au/media-releases"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find media releases
            articles = soup.find_all(['article', 'div', 'li'], limit=15)
            
            for article in articles:
                # Look for headings or links
                title_elem = article.find(['h2', 'h3', 'h4', 'a'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    # Filter for enforcement-related content
                    if any(keyword in title.lower() for keyword in ['court', 'penalty', 'proceeding', 'action', 'investigation', 'breach']):
                        enforcement.append({
                            'title': title[:300],
                            'source': 'ACCC'
                        })
            
            if enforcement:
                print(f"✓ Found {len(enforcement)} ACCC enforcement-related releases")
            else:
                # Get any recent releases even if not enforcement-specific
                all_links = soup.find_all('a', href=re.compile(r'/media-release/'))[:10]
                for link in all_links:
                    title = link.get_text(strip=True)
                    if len(title) > 15:
                        enforcement.append({
                            'title': title[:300],
                            'source': 'ACCC Media Release'
                        })
                
                if not enforcement:
                    enforcement = [{
                        'note': 'ACCC media releases page accessed',
                        'url': url
                    }]
                else:
                    print(f"✓ Found {len(enforcement)} ACCC media releases")
        
    except Exception as e:
        print(f"✗ Error fetching ACCC data: {str(e)}")
        enforcement = [{
            'error': str(e)[:200],
            'source': 'ACCC'
        }]
    
    return enforcement

def fetch_asx_announcements():
    """
    Monitor ASX announcements - Note: ASX data typically requires subscription
    """
    announcements = []
    
    try:
        # ASX Company announcements are behind a paywall/require subscription
        # But we can check the main news page
        url = "https://www2.asx.com.au/markets/news"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find any public news items
            news_items = soup.find_all(['article', 'div'], class_=re.compile(r'news|announcement'))[:10]
            
            for item in news_items:
                title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 10:
                        announcements.append({
                            'title': title[:300],
                            'source': 'ASX News'
                        })
            
            if announcements:
                print(f"✓ Found {len(announcements)} ASX news items")
            else:
                announcements = [{
                    'note': 'ASX price-sensitive announcements require market data subscription',
                    'recommendation': 'Consider: IRESS, Morningstar, or direct ASX data feed',
                    'free_alternative': 'Monitor specific company pages or Google Finance alerts',
                    'url': 'https://www2.asx.com.au/'
                }]
        
    except Exception as e:
        print(f"✗ Error fetching ASX data: {str(e)}")
        announcements = [{
            'error': str(e)[:200],
            'note': 'ASX data typically requires subscription',
            'source': 'ASX'
        }]
    
    return announcements

def fetch_austlii_cases():
    """
    Search AustLII for recent significant cases
    """
    cases = []
    
    try:
        # AustLII recent cases
        # Try Federal Court database
        url = "http://www8.austlii.edu.au/cgi-bin/viewdb/au/cases/cth/FCA/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find case links
            case_links = soup.find_all('a', href=re.compile(r'/cth/FCA/\d{4}/'))[:15]
            
            for link in case_links:
                case_text = link.get_text(strip=True)
                if len(case_text) > 10:
                    cases.append({
                        'case': case_text[:300],
                        'url': 'http://www.austlii.edu.au' + link.get('href', ''),
                        'database': 'FCA (Federal Court)'
                    })
            
            if cases:
                print(f"✓ Found {len(cases)} recent Federal Court cases on AustLII")
            else:
                cases = [{
                    'note': 'AustLII accessible - configure specific database searches',
                    'databases': ['FCA', 'NSWSC', 'VSC', 'QSC'],
                    'url': 'http://www.austlii.edu.au/'
                }]
        
    except Exception as e:
        print(f"✗ Error fetching AustLII data: {str(e)}")
        cases = [{
            'error': str(e)[:200],
            'source': 'AustLII',
            'note': 'Free resource but may need specific search configuration'
        }]
    
    return cases

def fetch_abc_news_business():
    """
    Fetch ABC News Business section for corporate/legal news
    Bonus source for context
    """
    news = []
    
    try:
        url = "https://www.abc.net.au/news/business/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles
            articles = soup.find_all(['article', 'a'], limit=15)
            
            for article in articles:
                title_elem = article.find(['h3', 'h2', 'span']) or article
                title = title_elem.get_text(strip=True)
                
                # Filter for business/legal relevant news
                if len(title) > 20 and any(keyword in title.lower() for keyword in 
                    ['company', 'court', 'asic', 'accc', 'administration', 'bankruptcy', 
                     'lawsuit', 'regulator', 'fine', 'investigation']):
                    news.append({
                        'headline': title[:300],
                        'source': 'ABC News Business'
                    })
            
            if news:
                print(f"✓ Found {len(news)} relevant ABC business news items")
        
    except Exception as e:
        print(f"⚠ Could not fetch ABC News: {str(e)}")
    
    return news

def generate_briefing():
    """
    Collect all data and generate briefing using Claude
    """
    print("\n" + "="*70)
    print("COLLECTING AUSTRALIAN LEGAL INTELLIGENCE DATA")
    print("="*70 + "\n")
    
    # Collect data from all sources
    print("Fetching ASIC insolvency notices...")
    asic_insolvency = fetch_asic_insolvency_notices()
    time.sleep(1)  # Be polite to servers
    
    print("Fetching ASIC announcements...")
    asic_announcements = fetch_asic_company_announcements()
    time.sleep(1)
    
    print("Fetching Federal Court notices...")
    federal_court = fetch_federal_court_notices()
    time.sleep(1)
    
    print("Fetching ACCC enforcement actions...")
    accc_enforcement = fetch_accc_enforcement()
    time.sleep(1)
    
    print("Fetching ASX announcements...")
    asx_announcements = fetch_asx_announcements()
    time.sleep(1)
    
    print("Fetching AustLII cases...")
    austlii_cases = fetch_austlii_cases()
    time.sleep(1)
    
    print("Fetching ABC News business...")
    abc_news = fetch_abc_news_business()
    
    print("\n" + "="*70)
    print("DATA COLLECTION COMPLETE")
    print("="*70 + "\n")
    
    # Format data for Claude
    data_summary = f"""
=== ASIC INSOLVENCY NOTICES ===
{json.dumps(asic_insolvency, indent=2)}

=== ASIC ANNOUNCEMENTS & MEDIA RELEASES ===
{json.dumps(asic_announcements, indent=2)}

=== FEDERAL COURT FILINGS & JUDGMENTS ===
{json.dumps(federal_court, indent=2)}

=== ACCC ENFORCEMENT ACTIONS ===
{json.dumps(accc_enforcement, indent=2)}

=== ASX ANNOUNCEMENTS ===
{json.dumps(asx_announcements, indent=2)}

=== AUSTLII RECENT CASES ===
{json.dumps(austlii_cases, indent=2)}

=== ABC NEWS BUSINESS (Context) ===
{json.dumps(abc_news, indent=2)}
"""
    
    print("Generating briefing with Claude...")
    
    # Check API key exists
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        error_message = f"""
ERROR: ANTHROPIC_API_KEY NOT FOUND
==================================
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The ANTHROPIC_API_KEY environment variable is not set.

Please check:
1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Ensure 'ANTHROPIC_API_KEY' exists and has your Claude API key
4. The secret name must be exactly 'ANTHROPIC_API_KEY' (case-sensitive)

Data collected:
{data_summary}
"""
        print(error_message)
        return error_message
    
    # Verify API key format
    if not api_key.startswith('sk-ant-'):
        error_message = f"""
ERROR: INVALID API KEY FORMAT
==============================
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The API key doesn't appear to be valid. Anthropic API keys should start with 'sk-ant-'

Current key starts with: {api_key[:10]}...

Please verify:
1. You're using your Anthropic API key (not OpenAI or another service)
2. Get your key from: https://console.anthropic.com/settings/keys
3. Copy the entire key including the 'sk-ant-' prefix

Data collected:
{data_summary}
"""
        print(error_message)
        return error_message
    
    # Call Claude API
    try:
        print(f"✓ API Key verified (starts with: {api_key[:15]}...)")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"""You are a senior legal intelligence analyst for a top-tier Australian commercial law firm specializing in disputes, insolvency, and regulatory matters.

Analyze this data collected from Australian sources on {datetime.now().strftime('%A, %d %B %Y')}:

{data_summary}

Provide a comprehensive morning briefing with:

## EXECUTIVE SUMMARY
Brief overview (2-3 sentences) of the most significant opportunities and trends identified today.

## HIGH-PRIORITY OPPORTUNITIES
Rank and describe specific matters worth pursuing:
- Companies entering external administration (with estimated value/creditor exposure if mentioned)
- Significant regulatory enforcement actions with class action potential
- Federal Court matters indicating commercial disputes
- Director changes or corporate announcements suggesting financial distress
- Any emerging litigation patterns

For each opportunity, note: company name, jurisdiction, matter type, estimated value (if available), and why it's relevant.

## MARKET INTELLIGENCE
- Industries showing signs of stress
- Regulatory enforcement trends (ASIC, ACCC focus areas)
- Notable case law developments
- Competitor activity (if other law firms are mentioned)

## EMERGING TRENDS
Identify patterns across:
- Industry sectors
- Types of insolvency/administration
- Regulatory focus areas
- Geographic concentrations

## NEWS CONTEXT
Relevant business news that may indicate future legal work (corporate restructures, regulatory changes, etc.)

## RECOMMENDED ACTIONS
Specific, actionable next steps:
1. Companies to contact immediately
2. Matters requiring further investigation
3. Conflicts checks needed
4. Areas for deeper monitoring

## DATA QUALITY NOTES
Brief assessment of which data sources provided useful intelligence vs. which need configuration improvements.

Be analytical and strategic. Focus on revenue-generating opportunities. Where actual company names, case numbers, or specific details are available, include them. Where data is limited or placeholder, note it briefly but still provide strategic value from available information."""
            }]
        )
        
        briefing_text = message.content[0].text
        print("✓ Briefing generated successfully!\n")
        return briefing_text
        
    except anthropic.AuthenticationError as e:
        error_message = f"""
ERROR: AUTHENTICATION FAILED
============================
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Error: {str(e)}

Your API key was rejected by Anthropic.

Please verify:
1. The API key is active at: https://console.anthropic.com/settings/keys
2. You have credits available in your account
3. You copied the complete key (they're quite long)

Data collected:
{data_summary}
"""
        print(error_message)
        return error_message
        
    except anthropic.RateLimitError as e:
        error_message = f"""
ERROR: RATE LIMIT EXCEEDED
==========================
Time:
