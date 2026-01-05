import anthropic
import requests
from datetime import datetime, timedelta
import os
import json
from bs4 import BeautifulSoup
import time
import re
import traceback
from urllib.parse import quote_plus

def fetch_google_news_by_topic(topic, region='AU', language='en'):
    """
    Fetch Google News for a specific legal topic in Australia
    """
    articles = []
    
    try:
        # Google News RSS feed
        query = f"{topic} Australia"
        encoded_query = quote_plus(query)
        
        # Google News RSS URL
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={language}&gl={region}&ceid={region}:{language}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')  # Note: 'xml' parser for RSS
            
            items = soup.find_all('item')[:10]  # Top 10 results per topic
            
            for item in items:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                source = item.find('source')
                
                if title:
                    article = {
                        'title': title.get_text(strip=True)[:300],
                        'link': link.get_text(strip=True) if link else '',
                        'date': pub_date.get_text(strip=True) if pub_date else '',
                        'source': source.get_text(strip=True) if source else 'Unknown',
                        'topic': topic
                    }
                    articles.append(article)
            
            return articles
        else:
            print(f"  ⚠ Google News {topic}: HTTP {response.status_code}")
            return []
        
    except Exception as e:
        print(f"  ✗ Google News {topic} error: {str(e)[:100]}")
        return []

def fetch_comprehensive_google_news():
    """
    Fetch Google News across all practice areas
    """
    print("  Fetching comprehensive Google News coverage...")
    
    # Define practice area search terms
    topics = [
        # Insolvency & Restructuring
        "insolvency",
        "liquidation",
        "voluntary administration",
        "receivership",
        "restructuring",
        "bankruptcy",
        "external administration",
        
        # Regulatory & Compliance
        "ASIC enforcement",
        "ACCC penalty",
        "AML CTF compliance",
        "anti-money laundering Australia",
        "financial services regulation",
        
        # Workplace & Employment
        "workplace safety prosecution",
        "unfair dismissal",
        "employment law dispute",
        "redundancies Australia",
        "WorkCover prosecution",
        "Fair Work Commission",
        
        # Litigation & Disputes
        "class action Australia",
        "commercial litigation",
        "shareholder dispute",
        "breach of contract Australia",
        "Federal Court proceedings",
        
        # ADR
        "arbitration Australia",
        "mediation settlement",
        "dispute resolution",
        
        # Construction & Security of Payment
        "security of payment",
        "construction dispute Australia",
        "building industry payment",
        
        # Corporate & Governance
        "director penalties",
        "corporate governance breach",
        "insolvent trading"
    ]
    
    all_articles = []
    
    for i, topic in enumerate(topics):
        print(f"    [{i+1}/{len(topics)}] Searching: {topic}")
        
        articles = fetch_google_news_by_topic(topic)
        
        if articles:
            all_articles.extend(articles)
            print(f"      ✓ Found {len(articles)} articles")
        else:
            print(f"      - No results")
        
        # Rate limiting - be respectful to Google
        time.sleep(2)
    
    # Remove duplicates based on title
    seen_titles = set()
    unique_articles = []
    
    for article in all_articles:
        title_key = article['title'][:100].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)
    
    print(f"\n  ✓ Total: {len(all_articles)} articles found, {len(unique_articles)} unique")
    
    return unique_articles

def fetch_targeted_google_news():
    """
    Faster version with combined searches for key topics
    """
    print("  Fetching targeted Google News...")
    
    # Combined searches for efficiency
    search_queries = [
        "insolvency OR liquidation OR administration Australia",
        "ASIC OR ACCC enforcement penalty Australia",
        "AML CTF compliance Australia",
        "workplace safety OR employment law Australia",
        "class action OR litigation Australia",
        "security of payment construction Australia",
        "arbitration OR mediation dispute Australia"
    ]
    
    all_articles = []
    
    for i, query in enumerate(search_queries):
        print(f"    [{i+1}/{len(search_queries)}] {query[:50]}...")
        
        try:
            encoded_query = quote_plus(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=AU&ceid=AU:en"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')[:15]  # More results for combined searches
                
                for item in items:
                    title = item.find('title')
                    link = item.find('link')
                    pub_date = item.find('pubDate')
                    source = item.find('source')
                    
                    if title:
                        article = {
                            'title': title.get_text(strip=True)[:300],
                            'link': link.get_text(strip=True) if link else '',
                            'date': pub_date.get_text(strip=True)[:50] if pub_date else '',
                            'source': source.get_text(strip=True) if source else 'Unknown',
                            'search_query': query[:50]
                        }
                        all_articles.append(article)
                
                print(f"      ✓ Found {len(items)} articles")
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"      ✗ Error: {str(e)[:100]}")
            continue
    
    # Remove duplicates
    seen_titles = set()
    unique_articles = []
    
    for article in all_articles:
        title_key = article['title'][:100].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)
    
    print(f"  ✓ Total: {len(unique_articles)} unique articles\n")
    
    return unique_articles

def fetch_asic_insolvency_notices():
    """
    ASIC insolvency notices
    """
    notices = []
    
    try:
        base_url = "https://insolvencynotices.asic.gov.au"
        search_url = f"{base_url}/browsesearch-notices/notice-search"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-AU,en;q=0.9',
            'Referer': base_url
        }
        
        session = requests.Session()
        session.get(base_url, headers=headers, timeout=15)
        time.sleep(1)
        
        response = session.get(search_url, headers=headers, timeout=15)
        
        print(f"  ASIC Insolvency Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            notice_rows = soup.find_all(['tr', 'div'], class_=re.compile(r'notice|result|row'), limit=20)
            
            for row in notice_rows:
                text = row.get_text(strip=True)
                if len(text) > 40:
                    if any(indicator in text for indicator in ['PTY', 'LTD', 'LIMITED', 'ACN', 'ABN']):
                        notices.append({
                            'text': text[:400],
                            'source': 'ASIC Insolvency Notices'
                        })
            
            if notices:
                print(f"  ✓ Found {len(notices)} insolvency notices")
            else:
                notices = [{
                    'status': 'Page accessible - requires manual search',
                    'url': search_url
                }]
                print(f"  ⚠ ASIC accessible but needs config")
        else:
            notices = [{'status': f'HTTP {response.status_code}'}]
        
    except Exception as e:
        print(f"  ✗ ASIC error: {str(e)[:100]}")
        notices = [{'error': str(e)[:200]}]
    
    return notices

def fetch_asic_company_announcements():
    """
    ASIC media releases
    """
    announcements = []
    
    try:
        url = "https://asic.gov.au/about-asic/news-centre/find-a-media-release/find-a-media-release/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        print(f"  ASIC Media Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items = (
                soup.find_all('article') or
                soup.find_all('div', class_=re.compile(r'media|release|news')) or
                soup.find_all('li', class_=re.compile(r'media|release'))
            )
            
            for item in items[:20]:
                title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 25:
                        date_elem = item.find(['time', 'span'], class_=re.compile(r'date|time'))
                        date_text = date_elem.get_text(strip=True) if date_elem else ''
                        
                        announcements.append({
                            'title': title[:300],
                            'date': date_text[:50],
                            'source': 'ASIC'
                        })
            
            if announcements:
                print(f"  ✓ Found {len(announcements)} ASIC releases")
            else:
                announcements = [{'status': 'Page accessible but structure changed'}]
                print(f"  ⚠ ASIC needs parser update")
        
    except Exception as e:
        print(f"  ✗ ASIC error: {str(e)[:100]}")
        announcements = [{'error': str(e)[:200]}]
    
    return announcements

def fetch_accc_enforcement():
    """
    ACCC enforcement actions
    """
    enforcement = []
    
    try:
        urls = [
            "https://www.accc.gov.au/about-us/media/media-releases",
            "https://www.accc.gov.au/media-releases"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
                
                print(f"  ACCC trying {url.split('/')[-1]}: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    items = soup.find_all(['article', 'div', 'li'], limit=40)
                    
                    for item in items:
                        title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                        if title_elem:
                            text = title_elem.get_text(strip=True)
                            if len(text) > 25:
                                if any(keyword in text.lower() for keyword in 
                                    ['court', 'penalty', 'fine', 'action', 'proceeding',
                                     'breach', 'investigation', 'enforcement', 'undertaking']):
                                    enforcement.append({
                                        'title': text[:300],
                                        'source': 'ACCC Enforcement'
                                    })
                    
                    if enforcement:
                        print(f"  ✓ Found {len(enforcement)} ACCC items")
                        break
                    
            except Exception:
                continue
        
        if not enforcement:
            enforcement = [{'status': 'No content found'}]
            print(f"  ⚠ ACCC - no content")
        
    except Exception as e:
        print(f"  ✗ ACCC error: {str(e)[:100]}")
        enforcement = [{'error': str(e)[:200]}]
    
    return enforcement

def fetch_austlii_federal_court():
    """
    Federal Court cases via AustLII
    """
    cases = []
    
    try:
        current_year = datetime.now().year
        urls = [
            f"http://www8.austlii.edu.au/cgi-bin/viewdb/au/cases/cth/FCA/{current_year}/",
            f"http://www8.austlii.edu.au/cgi-bin/viewdb/au/cases/cth/FCA/{current_year-1}/"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=15)
                year = url.split('/')[-2]
                
                print(f"  AustLII FCA {year} Status: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    case_links = soup.find_all('a', href=re.compile(r'\d+\.html'))
                    
                    limit = 20 if year == str(current_year) else 10
                    recent_cases = case_links[-limit:] if year == str(current_year - 1) else case_links[:limit]
                    
                    for link in recent_cases:
                        case_name = link.get_text(strip=True)
                        if len(case_name) > 15:
                            text_lower = case_name.lower()
                            if any(keyword in text_lower for keyword in 
                                ['corporation', 'insolvency', 'asic', 'accc', 'liquidat',
                                 'administration', 'bankruptcy', 'employment', 'workplace']):
                                cases.append({
                                    'case': case_name[:400],
                                    'court': 'Federal Court of Australia',
                                    'source': 'AustLII',
                                    'year': year,
                                    'relevance': 'High'
                                })
                            elif len(cases) < 15:
                                cases.append({
                                    'case': case_name[:400],
                                    'court': 'Federal Court',
                                    'source': 'AustLII',
                                    'year': year
                                })
                    
                    if cases:
                        print(f"  ✓ Found {len([c for c in cases if c['year']==year])} FCA {year} cases")
                
            except Exception as e:
                print(f"  ⚠ AustLII FCA {year} error: {str(e)[:100]}")
                continue
        
        if not cases:
            cases = [{'status': 'AustLII accessible', 'instruction': 'Configure searches'}]
        
    except Exception as e:
        print(f"  ✗ AustLII error: {str(e)[:100]}")
        cases = [{'error': str(e)[:200]}]
    
    return cases

def fetch_abc_news_business():
    """
    ABC News Business
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
            
            articles = soup.find_all(['article', 'div', 'a'], limit=50)
            
            for article in articles:
                headline_elem = article.find(['h1', 'h2', 'h3', 'h4']) or article
                text = headline_elem.get_text(strip=True)
                
                if len(text) > 25:
                    if any(keyword in text.lower() for keyword in 
                        ['company', 'court', 'asic', 'accc', 'administration',
                         'liquidat', 'bankrupt', 'lawsuit', 'regulator',
                         'investigation', 'collapse', 'insolvency']):
                        news.append({
                            'headline': text[:300],
                            'source': 'ABC News Business'
                        })
            
            if news:
                print(f"  ✓ Found {len(news)} ABC news items")
        
    except Exception as e:
        print(f"  ⚠ ABC News error: {str(e)[:100]}")
    
    return news

def generate_briefing():
    """
    Generate comprehensive briefing with Google News
    """
    print("\n" + "="*70)
    print("COLLECTING AUSTRALIAN LEGAL INTELLIGENCE DATA")
    print("Google News + Public Sources")
    print("="*70 + "\n")
    
    # Collect data from all sources
    print("Fetching Google News (all practice areas)...")
    google_news = fetch_targeted_google_news()  # Use targeted for speed
    # Alternative: google_news = fetch_comprehensive_google_news()  # More thorough but slower
    time.sleep(1)
    
    print("Fetching ASIC insolvency notices...")
    asic_insolvency = fetch_asic_insolvency_notices()
    time.sleep(1)
    
    print("Fetching ASIC media releases...")
    asic_announcements = fetch_asic_company_announcements()
    time.sleep(1)
    
    print("Fetching ACCC enforcement actions...")
    accc_enforcement = fetch_accc_enforcement()
    time.sleep(1)
    
    print("Fetching Federal Court cases (AustLII)...")
    federal_court = fetch_austlii_federal_court()
    time.sleep(1)
    
    print("Fetching ABC News business...")
    abc_news = fetch_abc_news_business()
    
    print("\n" + "="*70)
    print("DATA COLLECTION COMPLETE")
    print("="*70 + "\n")
    
    # Organize Google News by practice area for better analysis
    practice_areas = {
        'Insolvency & Restructuring': [],
        'Regulatory & Compliance': [],
        'Workplace & Employment': [],
        'Litigation & Disputes': [],
        'ADR': [],
        'Construction & Security of Payment': [],
        'Corporate Governance': []
    }
    
    for article in google_news:
        title_lower = article['title'].lower()
        
        if any(kw in title_lower for kw in ['insolvency', 'liquidation', 'administration', 'receivership', 'restructuring', 'bankruptcy']):
            practice_areas['Insolvency & Restructuring'].append(article)
        elif any(kw in title_lower for kw in ['asic', 'accc', 'aml', 'ctf', 'compliance', 'regulation']):
            practice_areas['Regulatory & Compliance'].append(article)
        elif any(kw in title_lower for kw in ['workplace', 'employment', 'unfair dismissal', 'redundanc', 'fair work']):
            practice_areas['Workplace & Employment'].append(article)
        elif any(kw in title_lower for kw in ['class action', 'litigation', 'lawsuit', 'proceeding']):
            practice_areas['Litigation & Disputes'].append(article)
        elif any(kw in title_lower for kw in ['arbitration', 'mediation', 'dispute resolution']):
            practice_areas['ADR'].append(article)
        elif any(kw in title_lower for kw in ['security of payment', 'construction dispute', 'building']):
            practice_areas['Construction & Security of Payment'].append(article)
        elif any(kw in title_lower for kw in ['director', 'governance', 'insolvent trading']):
            practice_areas['Corporate Governance'].append(article)
    
    # Format data for Claude
    data_summary = f"""
=== GOOGLE NEWS BY PRACTICE AREA ===

INSOLVENCY & RESTRUCTURING ({len(practice_areas['Insolvency & Restructuring'])} articles):
{json.dumps(practice_areas['Insolvency & Restructuring'], indent=2)}

REGULATORY & COMPLIANCE ({len(practice_areas['Regulatory & Compliance'])} articles):
{json.dumps(practice_areas['Regulatory & Compliance'], indent=2)}

WORKPLACE & EMPLOYMENT ({len(practice_areas['Workplace & Employment'])} articles):
{json.dumps(practice_areas['Workplace & Employment'], indent=2)}

LITIGATION & DISPUTES ({len(practice_areas['Litigation & Disputes'])} articles):
{json.dumps(practice_areas['Litigation & Disputes'], indent=2)}

ADR (ARBITRATION/MEDIATION) ({len(practice_areas['ADR'])} articles):
{json.dumps(practice_areas['ADR'], indent=2)}

CONSTRUCTION & SECURITY OF PAYMENT ({len(practice_areas['Construction & Security of Payment'])} articles):
{json.dumps(practice_areas['Construction & Security of Payment'], indent=2)}

CORPORATE GOVERNANCE ({len(practice_areas['Corporate Governance'])} articles):
{json.dumps(practice_areas['Corporate Governance'], indent=2)}

=== ASIC INSOLVENCY NOTICES ===
{json.dumps(asic_insolvency, indent=2)}

=== ASIC MEDIA RELEASES ===
{json.dumps(asic_announcements, indent=2)}

=== ACCC ENFORCEMENT ACTIONS ===
{json.dumps(accc_enforcement, indent=2)}

=== FEDERAL COURT CASES (AustLII) ===
{json.dumps(federal_court, indent=2)}

=== ABC NEWS BUSINESS ===
{json.dumps(abc_news, indent=2)}
"""
    
    print("Generating briefing with Claude...")
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY not found"
    
    if not api_key.startswith('sk-ant-'):
        return "ERROR: Invalid API key format"
    
    # Call Claude
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=6000,
            messages=[{
                "role": "user",
                "content": f"""You are a senior legal intelligence analyst for a top-tier Australian commercial law firm with practice areas in: Insolvency & Restructuring, Regulatory Compliance, Workplace Law, Litigation, ADR, Construction, and Corporate Governance.

Analyze this comprehensive data collected from Google News and Australian public sources on {datetime.now().strftime('%A, %d %B %Y')}:

{data_summary}

Provide a detailed morning briefing with:

## EXECUTIVE SUMMARY
3-4 sentences highlighting the most significant revenue opportunities across all practice areas.

## HIGH-PRIORITY OPPORTUNITIES BY PRACTICE AREA

### INSOLVENCY & RESTRUCTURING
- Specific companies entering administration/liquidation
- Estimated creditor exposure or matter value
- Source and immediate actions

### REGULATORY & COMPLIANCE
- ASIC/ACCC enforcement actions with class action potential
- AML/CTF breaches or investigations
- Companies facing regulatory scrutiny

### WORKPLACE & EMPLOYMENT LAW
- Major unfair dismissal cases
- Mass redundancies
- Workplace safety prosecutions
- Fair Work Commission matters

### LITIGATION & DISPUTES
- Class actions (actual or potential)
- Significant commercial disputes
- Federal Court proceedings

### CONSTRUCTION & SECURITY OF PAYMENT
- Payment disputes
- Construction company collapses
- Security of payment claims

### ADR
- Notable arbitration or mediation matters
- Dispute resolution opportunities

### CORPORATE GOVERNANCE
- Director penalty matters
- Insolvent trading allegations
- Governance breaches

## MARKET INTELLIGENCE
- Industries under stress by practice area
- Regulatory enforcement trends
- Emerging legal risks

## MEDIA ANALYSIS
Key themes from Google News coverage with business development implications.

## RECOMMENDED ACTIONS
### Immediate (Today)
1. Companies to contact (by practice area)
2. Urgent conflicts checks
3. Client alerts to prepare

### This Week
1. Follow-up investigations
2. Business development opportunities
3. Market monitoring

## DATA SOURCE PERFORMANCE
Rate each source (⭐⭐⭐⭐⭐ to ❌):
- Google News (by practice area coverage)
- ASIC Insolvency Notices
- ASIC Media Releases
- ACCC Enforcement
- Federal Court (AustLII)
- ABC News Business

Note which practice areas have strong vs. weak intelligence coverage.

Be specific with company names, amounts, case names. Focus on actionable revenue opportunities across all practice areas."""
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"briefing_{timestamp}.txt"
        
        header = f"""AUSTRALIAN LEGAL INTELLIGENCE BRIEFING
Generated: {datetime.now().strftime('%A, %d %B %Y at %H:%M AEST')}
Practice Areas: Insolvency, Regulatory, Workplace, Litigation, ADR, Construction, Governance
Sources: Google News, ASIC, ACCC, Federal Court, ABC News
{'='*70}

"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(briefing)
        
        with open('briefing.txt', 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(briefing)
        
        print(f"✓ Briefing saved to {filename}")
        return filename
        
    except Exception as e:
        print(f"✗ Error saving: {str(e)}")
        return None

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AUSTRALIAN LEGAL INTELLIGENCE AGENT")
    print("Multi-Practice Area Edition: Google News Integration")
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
