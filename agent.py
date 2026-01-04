import anthropic
import requests
from datetime import datetime, timedelta
import os
import json
from bs4 import BeautifulSoup
import time
import re
import traceback

def fetch_asic_insolvency_notices():
    """
    Fetch recent ASIC insolvency notices
    """
    notices = []
    try:
        # Try the main search page
        url = "https://insolvencynotices.asic.gov.au/browsesearch-notices/notice-search"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-AU,en;q=0.9',
        }
        
        # Try GET first, then POST if that fails
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        print(f"  ASIC Insolvency Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for notice listings
            notice_rows = soup.find_all(['tr', 'div'], class_=re.compile(r'notice|result|item'))
            
            for row in notice_rows[:15]:
                text = row.get_text(strip=True)
                if len(text) > 30:
                    notices.append({
                        'text': text[:300],
                        'source': 'ASIC Insolvency Notices'
                    })
            
            if notices:
                print(f"  ✓ Found {len(notices)} insolvency notices")
            else:
                # Even if we can't parse notices, note the page is accessible
                notices = [{
                    'status': 'Page accessible - requires specific search parameters',
                    'url': url,
                    'note': 'Manual configuration needed for date range searches'
                }]
                print(f"  ⚠ Page accessible but needs search configuration")
        else:
            notices = [{
                'status': f'HTTP {response.status_code}',
                'url': url,
                'note': 'May require session cookies or CAPTCHA'
            }]
            
    except Exception as e:
        print(f"  ✗ ASIC Insolvency error: {str(e)[:100]}")
        notices = [{'error': str(e)[:200], 'source': 'ASIC Insolvency'}]
    
    return notices

def fetch_asic_company_announcements():
    """
    Fetch ASIC media releases with better parsing
    """
    announcements = []
    
    try:
        url = "https://asic.gov.au/about-asic/news-centre/find-a-media-release/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-AU,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        print(f"  ASIC Media Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors
            article_elements = (
                soup.find_all('article') or 
                soup.find_all('div', class_=re.compile(r'media|release|news|item')) or
                soup.find_all('li', class_=re.compile(r'media|release|news'))
            )
            
            for article in article_elements[:15]:
                # Look for titles/headings
                title_elem = (
                    article.find('h2') or 
                    article.find('h3') or 
                    article.find('h4') or
                    article.find('a', class_=re.compile(r'title|heading'))
                )
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 20:
                        # Try to find date
                        date_elem = article.find('time') or article.find(class_=re.compile(r'date|time'))
                        date_str = date_elem.get_text(strip=True) if date_elem else 'Date unknown'
                        
                        announcements.append({
                            'title': title[:250],
                            'date': date_str[:50],
                            'source': 'ASIC Media Release'
                        })
            
            if announcements:
                print(f"  ✓ Found {len(announcements)} ASIC media releases")
            else:
                # Try to get any links
                all_links = soup.find_all('a', href=re.compile(r'media-release|news'))[:10]
                for link in all_links:
                    text = link.get_text(strip=True)
                    if len(text) > 20:
                        announcements.append({
                            'title': text[:250],
                            'source': 'ASIC'
                        })
                
                if announcements:
                    print(f"  ✓ Found {len(announcements)} ASIC items via links")
                else:
                    announcements = [{'status': 'Page accessible', 'url': url, 'note': 'HTML structure may have changed'}]
                    print(f"  ⚠ Page accessible but content structure changed")
        else:
            announcements = [{'status': f'HTTP {response.status_code}', 'url': url}]
        
    except Exception as e:
        print(f"  ✗ ASIC announcements error: {str(e)[:100]}")
        announcements = [{'error': str(e)[:200]}]
    
    return announcements

def fetch_federal_court_notices():
    """
    Fetch Federal Court recent judgments
    """
    filings = []
    
    try:
        # Try the judgments search page
        url = "https://www.fedcourt.gov.au/digital-law-library/judgments/search"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        print(f"  Federal Court Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for case listings
            case_links = soup.find_all('a', href=re.compile(r'/judgment/|/case/'))[:15]
            
            for link in case_links:
                text = link.get_text(strip=True)
                if len(text) > 15:
                    filings.append({
                        'case': text[:300],
                        'url': link.get('href', '')[:200],
                        'source': 'Federal Court'
                    })
            
            if filings:
                print(f"  ✓ Found {len(filings)} Federal Court cases")
            else:
                filings = [{
                    'status': 'Page accessible',
                    'url': url,
                    'note': 'Configure search parameters for specific practice areas'
                }]
                print(f"  ⚠ Page accessible but needs search config")
        elif response.status_code == 403:
            filings = [{
                'status': 'HTTP 403 - Access Forbidden',
                'note': 'May require IP whitelisting or different access method',
                'alternative': 'Try AustLII for Federal Court cases'
            }]
            print(f"  ✗ Federal Court blocked (403)")
        else:
            filings = [{'status': f'HTTP {response.status_code}', 'url': url}]
        
    except Exception as e:
        print(f"  ✗ Federal Court error: {str(e)[:100]}")
        filings = [{'error': str(e)[:200]}]
    
    return filings

def fetch_accc_enforcement():
    """
    Fetch ACCC media releases with better error handling
    """
    enforcement = []
    
    try:
        url = "https://www.accc.gov.au/media-releases"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        print(f"  ACCC Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for media releases
            items = (
                soup.find_all('article') or
                soup.find_all('div', class_=re.compile(r'media|release|news')) or
                soup.find_all('li')
            )
            
            for item in items[:30]:
                title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                if title_elem:
                    text = title_elem.get_text(strip=True)
                    if len(text) > 20:
                        # Filter for enforcement content
                        if any(keyword in text.lower() for keyword in 
                            ['court', 'penalty', 'action', 'proceeding', 'fine', 'breach', 'investigation', 'enforcement']):
                            enforcement.append({
                                'title': text[:250],
                                'source': 'ACCC Enforcement'
                            })
                        elif len(enforcement) < 5:  # Include some general releases too
                            enforcement.append({
                                'title': text[:250],
                                'source': 'ACCC'
                            })
            
            if enforcement:
                print(f"  ✓ Found {len(enforcement)} ACCC items")
            else:
                enforcement = [{'status': 'Page accessible', 'url': url, 'note': 'Content structure changed'}]
                print(f"  ⚠ ACCC page accessible but content not parsed")
        elif response.status_code == 404:
            enforcement = [{
                'status': 'HTTP 404 - URL may have changed',
                'try_instead': 'https://www.accc.gov.au/about-us/media'
            }]
            print(f"  ✗ ACCC 404 - URL changed")
        else:
            enforcement = [{'status': f'HTTP {response.status_code}', 'url': url}]
        
    except Exception as e:
        print(f"  ✗ ACCC error: {str(e)[:100]}")
        enforcement = [{'error': str(e)[:200]}]
    
    return enforcement

def fetch_austlii_federal_court():
    """
    Fetch recent Federal Court cases from AustLII (free alternative)
    """
    cases = []
    
    try:
        # Recent FCA cases
        url = "http://www8.austlii.edu.au/cgi-bin/viewdb/au/cases/cth/FCA/2025/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"  AustLII FCA Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find case links
            case_links = soup.find_all('a', href=re.compile(r'\d+\.html'))[:20]
            
            for link in case_links:
                case_name = link.get_text(strip=True)
                if len(case_name) > 10:
                    cases.append({
                        'case': case_name[:300],
                        'court': 'Federal Court of Australia',
                        'source': 'AustLII',
                        'year': '2025'
                    })
            
            if cases:
                print(f"  ✓ Found {len(cases)} recent FCA cases on AustLII")
            else:
                # Try 2024 cases
                url_2024 = "http://www8.austlii.edu.au/cgi-bin/viewdb/au/cases/cth/FCA/2024/"
                response_2024 = requests.get(url_2024, headers=headers, timeout=15)
                
                if response_2024.status_code == 200:
                    soup_2024 = BeautifulSoup(response_2024.content, 'html.parser')
                    case_links_2024 = soup_2024.find_all('a', href=re.compile(r'\d+\.html'))[-15:]  # Last 15 from 2024
                    
                    for link in case_links_2024:
                        case_name = link.get_text(strip=True)
                        if len(case_name) > 10:
                            cases.append({
                                'case': case_name[:300],
                                'court': 'Federal Court of Australia',
                                'source': 'AustLII',
                                'year': '2024 (recent)'
                            })
                    
                    if cases:
                        print(f"  ✓ Found {len(cases)} late 2024 FCA cases on AustLII")
        
        if not cases:
            cases = [{
                'status': 'AustLII accessible',
                'note': 'Free legal database - configure for specific searches',
                'databases': ['FCA 2025', 'FCA 2024', 'NSWSC', 'VSC', 'QSC'],
                'url': 'http://www.austlii.edu.au'
            }]
            print(f"  ⚠ AustLII accessible but needs configuration")
        
    except Exception as e:
        print(f"  ✗ AustLII error: {str(e)[:100]}")
        cases = [{'error': str(e)[:200], 'source': 'AustLII'}]
    
    return cases

def fetch_abc_news_business():
    """
    Fetch ABC News Business with better parsing
    """
    news = []
    
    try:
        url = "https://www.abc.net.au/news/business/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"  ABC News Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try various selectors
            articles = (
                soup.find_all('article') or
                soup.find_all('div', class_=re.compile(r'article|story|item')) or
                soup.find_all('a', class_=re.compile(r'article|story'))
            )
            
            for article in articles[:40]:
                # Find headline
                headline_elem = (
                    article.find('h3') or 
                    article.find('h2') or 
                    article.find('h4') or
                    article
                )
                
                text = headline_elem.get_text(strip=True)
                
                # Filter for business/legal keywords
                if len(text) > 25:
                    if any(keyword in text.lower() for keyword in 
                        ['company', 'companies', 'court', 'asic', 'accc', 'administration', 
                         'liquidat', 'bankrupt', 'lawsuit', 'regulator', 'fine', 'investigation',
                         'corporate', 'business', 'asx', 'shares', 'market']):
                        news.append({
                            'headline': text[:300],
                            'source': 'ABC News Business'
                        })
            
            if news:
                print(f"  ✓ Found {len(news)} ABC business news items")
            else:
                print(f"  ⚠ ABC News page accessible but no matching items")
        
    except Exception as e:
        print(f"  ⚠ ABC News error: {str(e)[:100]}")
    
    return news

def generate_briefing():
    """
    Collect all data and generate briefing
    """
    print("\n" + "="*70)
    print("COLLECTING AUSTRALIAN LEGAL INTELLIGENCE DATA")
    print("="*70 + "\n")
    
    # Collect data from all sources
    print("Fetching ASIC insolvency notices...")
    asic_insolvency = fetch_asic_insolvency_notices()
    time.sleep(1)
    
    print("Fetching ASIC announcements...")
    asic_announcements = fetch_asic_company_announcements()
    time.sleep(1)
    
    print("Fetching Federal Court notices...")
    federal_court = fetch_federal_court_notices()
    time.sleep(1)
    
    print("Fetching ACCC enforcement actions...")
    accc_enforcement = fetch_accc_enforcement()
    time.sleep(1)
    
    print("Fetching AustLII Federal Court cases...")
    austlii_cases = fetch_austlii_federal_court()
    time.sleep(1)
    
    print("Fetching ABC News business...")
    abc_news = fetch_abc_news_business()
    
    print("\n" + "="*70)
    print("DATA COLLECTION COMPLETE")
    print("="*70 + "\n")
    
    # ASX note
    asx_note = [{
        'note': 'ASX price-sensitive announcements require subscription',
        'options': 'IRESS, Morningstar, Bloomberg, or ASX direct feed',
        'free_alternative': 'Google Finance alerts for specific ASX codes'
    }]
    
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

=== AUSTLII FEDERAL COURT CASES ===
{json.dumps(austlii_cases, indent=2)}

=== ABC NEWS BUSINESS (Context) ===
{json.dumps(abc_news, indent=2)}

=== ASX ANNOUNCEMENTS ===
{json.dumps(asx_note, indent=2)}
"""
    
    print("Generating briefing with Claude...")
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY not found"
    
    if not api_key.startswith('sk-ant-'):
        return f"ERROR: Invalid API key format"
    
    # Call Claude
    try:
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
Brief overview highlighting the most significant opportunities and trends identified.

## HIGH-PRIORITY OPPORTUNITIES
List specific matters worth pursuing based on the data available. Include:
- Company names (if mentioned)
- Matter types
- Why each is relevant for business development
- Estimated value indicators (if available)

## MARKET INTELLIGENCE
- Industries showing activity or stress
- Regulatory enforcement trends from ACCC/ASIC
- Notable case developments from Federal Court/AustLII
- Business news context from ABC

## EMERGING TRENDS
Patterns across industries, enforcement areas, or case types.

## RECOMMENDED ACTIONS
Prioritized list of immediate actions:
1. Specific companies/matters to investigate
2. Conflicts checks needed
3. Data source improvements needed
4. Follow-up research required

## DATA SOURCE PERFORMANCE
Assess which sources provided actionable intelligence vs. which need improvement. Be specific about HTTP errors, access issues, or configuration needs.

Focus on extracting maximum value from available data. If data is limited, provide strategic recommendations for improving collection."""
            }]
        )
        
        briefing_text = message.content[0].text
        print("✓ Briefing generated successfully!\n")
        return briefing_text
        
    except Exception as e:
        return f"ERROR generating briefing: {str(e)}"

def save_briefing(briefing):
    """
    Save briefing to file
    """
    try:
        filename = f"briefing_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"AUSTRALIAN LEGAL INTELLIGENCE BRIEFING\n")
            f.write(f"Generated: {datetime.now().strftime('%A, %d %B %Y at %H:%M AEST')}\n")
            f.write("="*70 + "\n\n")
            f.write(briefing)
        
        with open('briefing.txt', 'w', encoding='utf-8') as f:
            f.write(f"AUSTRALIAN LEGAL INTELLIGENCE BRIEFING\n")
            f.write(f"Generated: {datetime.now().strftime('%A, %d %B %Y at %H:%M AEST')}\n")
            f.write("="*70 + "\n\n")
            f.write(briefing)
        
        print(f"✓ Briefing saved")
        return filename
        
    except Exception as e:
        print(f"✗ Error saving: {str(e)}")
        return None

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AUSTRALIAN LEGAL INTELLIGENCE AGENT")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    try:
        briefing = generate_briefing()
        save_briefing(briefing)
        
        print("\n" + "="*70)
        print("BRIEFING CONTENT")
        print("="*70 + "\n")
        print(briefing)
        print("\n" + "="*70)
        
        print("\n✓ Agent completed successfully!")
        
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {str(e)}")
        traceback.print_exc()
        exit(1)
