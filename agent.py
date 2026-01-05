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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def fetch_google_news_by_topic(topic, region='AU', language='en'):
    """
    Fetch Google News for a specific legal topic in Australia
    """
    articles = []
    
    try:
        query = f"{topic} Australia"
        encoded_query = quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={language}&gl={region}&ceid={region}:{language}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:10]
            
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
            return []
        
    except Exception as e:
        print(f"  ✗ Google News {topic} error: {str(e)[:100]}")
        return []

def fetch_targeted_google_news():
    """
    Targeted Google News searches - enhanced with more sources
    """
    print("  Fetching targeted Google News...")
    
    search_queries = [
        "insolvency OR liquidation OR administration Australia",
        "ASIC OR ACCC enforcement penalty Australia",
        "AML CTF compliance Australia",
        "workplace safety OR employment law Australia",
        "class action OR litigation Australia",
        "security of payment construction Australia",
        "arbitration OR mediation dispute Australia",
        "director duties OR insolvent trading Australia",  # Corporate governance
        "ASX announcement administration OR liquidation",   # ASX via news
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
                items = soup.find_all('item')[:15]
                
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
            
            time.sleep(2)
            
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

def fetch_asic_published_documents():
    """
    ASIC published documents - alternative to insolvency notices
    Includes media releases, reports, regulatory guides
    """
    documents = []
    
    try:
        # ASIC's download page often has recent documents
        url = "https://download.asic.gov.au/media/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"  ASIC Download Status: HTTP {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for document links
            links = soup.find_all('a', href=re.compile(r'\.(pdf|docx|html)'))[:20]
            
            for link in links:
                text = link.get_text(strip=True)
                href = link.get('href', '')
                
                if len(text) > 10:
                    documents.append({
                        'title': text[:300],
                        'url': href if href.startswith('http') else f"https://download.asic.gov.au{href}",
                        'source': 'ASIC Published Documents'
                    })
            
            if documents:
                print(f"  ✓ Found {len(documents)} ASIC documents")
        
        # Also try main ASIC news page
        news_url = "https://asic.gov.au/about-asic/news-centre/"
        news_response = requests.get(news_url, headers=headers, timeout=15)
        
        if news_response.status_code == 200:
            soup = BeautifulSoup(news_response.content, 'html.parser')
            
            # Find news items
            news_items = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'news|media|announcement'))[:15]
            
            for item in news_items:
                title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 20:
                        documents.append({
                            'title': title[:300],
                            'source': 'ASIC News Centre'
                        })
        
        if not documents:
            # Fallback: note that ASIC data is available via other means
            documents = [{
                'note': 'ASIC direct feed unavailable - using Google News for ASIC coverage',
                'alternative': 'Google News captures ASIC media releases and enforcement actions'
            }]
            print(f"  ⚠ ASIC - using Google News as primary source")
        else:
            print(f"  ✓ Total ASIC items: {len(documents)}")
        
    except Exception as e:
        print(f"  ✗ ASIC error: {str(e)[:100]}")
        documents = [{
            'note': 'ASIC websites inaccessible - relying on Google News coverage',
            'coverage': 'Google News includes ASIC media releases and enforcement announcements'
        }]
    
    return documents

def fetch_accc_public_registers():
    """
    ACCC public registers and alternative sources
    """
    items = []
    
    try:
        # Try multiple ACCC pages
        urls = [
            "https://www.accc.gov.au/public-registers/authorisations-and-notifications-registers",
            "https://www.accc.gov.au/about-us/publications",
            "https://www.accc.gov.au/business/business-rights-protections/public-registers"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
                
                print(f"  ACCC trying {url.split('/')[-1]}: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find links and content
                    links = soup.find_all('a', limit=30)
                    
                    for link in links:
                        text = link.get_text(strip=True)
                        if len(text) > 20:
                            if any(keyword in text.lower() for keyword in 
                                ['enforcement', 'penalty', 'court', 'undertaking', 
                                 'proceeding', 'action', 'compliance']):
                                items.append({
                                    'title': text[:300],
                                    'source': 'ACCC Public Register'
                                })
                    
                    if items:
                        print(f"      ✓ Found {len(items)} items")
                        break
                
            except Exception:
                continue
        
        if not items:
            items = [{
                'note': 'ACCC direct sources unavailable - using Google News for ACCC coverage',
                'coverage': 'Google News captures ACCC enforcement actions and media releases'
            }]
            print(f"  ⚠ ACCC - using Google News as primary source")
        
    except Exception as e:
        print(f"  ✗ ACCC error: {str(e)[:100]}")
        items = [{
            'note': 'Relying on Google News for ACCC enforcement intelligence'
        }]
    
    return items

def fetch_sbs_abc_business_news():
    """
    Enhanced news scraping from multiple free Australian sources
    """
    news = []
    
    sources = [
        {
            'name': 'ABC News Business',
            'url': 'https://www.abc.net.au/news/business/',
            'selectors': ['article', 'div']
        },
        {
            'name': 'SBS News Business',
            'url': 'https://www.sbs.com.au/news/topic/business',
            'selectors': ['article', 'div']
        },
        {
            'name': 'The Guardian Australia Business',
            'url': 'https://www.theguardian.com/australia-news/business',
            'selectors': ['article', 'div']
        },
        {
            'name': 'Nine News Business',
            'url': 'https://www.9news.com.au/business',
            'selectors': ['article', 'div']
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for source in sources:
        try:
            response = requests.get(source['url'], headers=headers, timeout=15)
            
            print(f"  {source['name']}: HTTP {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                articles = soup.find_all(source['selectors'], limit=50)
                
                source_count = 0
                for article in articles:
                    headline_elem = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    
                    if headline_elem:
                        text = headline_elem.get_text(strip=True)
                        
                        if len(text) > 25:
                            if any(keyword in text.lower() for keyword in 
                                ['company', 'court', 'asic', 'accc', 'administration',
                                 'liquidat', 'bankrupt', 'lawsuit', 'regulator',
                                 'investigation', 'collapse', 'insolvency', 'director',
                                 'asx', 'enforcement', 'penalty', 'fine']):
                                news.append({
                                    'headline': text[:300],
                                    'source': source['name']
                                })
                                source_count += 1
                
                if source_count > 0:
                    print(f"    ✓ Found {source_count} relevant articles")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"    ✗ {source['name']} error: {str(e)[:100]}")
            continue
    
    if news:
        print(f"  ✓ Total news items: {len(news)}\n")
    else:
        print(f"  ⚠ No news items found from free sources\n")
    
    return news

def fetch_asx_via_google_finance():
    """
    Monitor ASX-listed companies via Google Finance RSS
    Free alternative to paid ASX data feeds
    """
    asx_news = []
    
    try:
        # Monitor major ASX companies for relevant news
        # Focus on companies with higher insolvency/litigation risk
        sectors = [
            "ASX retail insolvency",
            "ASX construction administration",
            "ASX financial services ASIC",
            "ASX company receivership",
            "ASX mining liquidation"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for sector in sectors:
            try:
                encoded_query = quote_plus(sector)
                url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=AU&ceid=AU:en"
                
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')[:5]
                    
                    for item in items:
                        title = item.find('title')
                        if title:
                            asx_news.append({
                                'title': title.get_text(strip=True)[:300],
                                'sector': sector,
                                'source': 'ASX News (via Google)'
                            })
                
                time.sleep(2)
                
            except Exception:
                continue
        
        if asx_news:
            print(f"  ✓ Found {len(asx_news)} ASX-related news items")
        else:
            asx_news = [{
                'note': 'ASX monitoring via Google News - covers major announcements',
                'coverage': 'Administration, liquidation, regulatory actions for ASX companies'
            }]
            print(f"  ℹ ASX monitored via Google News")
        
    except Exception as e:
        print(f"  ✗ ASX monitoring error: {str(e)[:100]}")
        asx_news = [{'note': 'ASX news included in main Google News feed'}]
    
    return asx_news

def fetch_austlii_federal_court():
    """
    Federal Court cases via AustLII - enhanced
    """
    cases = []
    
    try:
        current_year = datetime.now().year
        
        # Try multiple AustLII databases
        databases = [
            {
                'name': 'Federal Court',
                'url': f"http://www8.austlii.edu.au/cgi-bin/viewdb/au/cases/cth/FCA/{current_year}/",
                'code': 'FCA'
            },
            {
                'name': 'NSW Supreme Court',
                'url': f"http://www8.austlii.edu.au/cgi-bin/viewdb/au/cases/nsw/NSWSC/{current_year}/",
                'code': 'NSWSC'
            },
            {
                'name': 'Victorian Supreme Court',
                'url': f"http://www8.austlii.edu.au/cgi-bin/viewdb/au/cases/vic/VSC/{current_year}/",
                'code': 'VSC'
            }
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for db in databases:
            try:
                response = requests.get(db['url'], headers=headers, timeout=15)
                
                print(f"  AustLII {db['code']} {current_year}: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    case_links = soup.find_all('a', href=re.compile(r'\d+\.html'))[:15]
                    
                    for link in case_links:
                        case_name = link.get_text(strip=True)
                        if len(case_name) > 15:
                            text_lower = case_name.lower()
                            
                            # Filter for relevant practice areas
                            if any(keyword in text_lower for keyword in 
                                ['corporation', 'insolvency', 'asic', 'accc', 'liquidat',
                                 'administration', 'bankruptcy', 'employment', 'workplace',
                                 'construction', 'payment', 'director', 'security']):
                                cases.append({
                                    'case': case_name[:400],
                                    'court': db['name'],
                                    'source': 'AustLII',
                                    'year': current_year,
                                    'relevance': 'High'
                                })
                    
                    if cases:
                        court_cases = [c for c in cases if c['court'] == db['name']]
                        print(f"    ✓ Found {len(court_cases)} {db['code']} cases")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"    ✗ {db['code']} error: {str(e)[:100]}")
                continue
        
        if not cases:
            cases = [{
                'status': 'AustLII accessible',
                'note': 'No recent cases matching practice area filters',
                'databases': ['FCA', 'NSWSC', 'VSC', 'QSC']
            }]
        else:
            print(f"  ✓ Total AustLII cases: {len(cases)}")
        
    except Exception as e:
        print(f"  ✗ AustLII error: {str(e)[:100]}")
        cases = [{'error': str(e)[:200]}]
    
    return cases

def generate_briefing():
    """
    Generate comprehensive briefing with all sources
    """
    print("\n" + "="*70)
    print("COLLECTING AUSTRALIAN LEGAL INTELLIGENCE DATA")
    print("Enhanced Multi-Source Edition")
    print("="*70 + "\n")
    
    # Collect data from all sources
    print("Fetching Google News (all practice areas)...")
    google_news = fetch_targeted_google_news()
    time.sleep(1)
    
    print("Fetching ASIC published documents...")
    asic_docs = fetch_asic_published_documents()
    time.sleep(1)
    
    print("Fetching ACCC public registers...")
    accc_items = fetch_accc_public_registers()
    time.sleep(1)
    
    print("Fetching ASX news (via Google)...")
    asx_news = fetch_asx_via_google_finance()
    time.sleep(1)
    
    print("Fetching Federal Court cases (AustLII - multiple courts)...")
    federal_court = fetch_austlii_federal_court()
    time.sleep(1)
    
    print("Fetching news from free Australian sources...")
    aus_news = fetch_sbs_abc_business_news()
    
    print("\n" + "="*70)
    print("DATA COLLECTION COMPLETE")
    print("="*70 + "\n")
    
    # Organize Google News by practice area
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
        elif any(kw in title_lower for kw in ['director', 'governance', 'insolvent trading', 'director duties']):
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

=== ASIC INTELLIGENCE ===
{json.dumps(asic_docs, indent=2)}

=== ACCC INTELLIGENCE ===
{json.dumps(accc_items, indent=2)}

=== ASX COMPANY NEWS ===
{json.dumps(asx_news, indent=2)}

=== COURT CASES (AustLII - FCA, NSWSC, VSC) ===
{json.dumps(federal_court, indent=2)}

=== AUSTRALIAN BUSINESS NEWS (ABC, SBS, Guardian, Nine) ===
{json.dumps(aus_news, indent=2)}
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

Analyze this comprehensive data collected from Google News, ASIC, ACCC, ASX, AustLII and Australian news sources on {datetime.now().strftime('%A, %d %B %Y')}:

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
- Court proceedings

### CONSTRUCTION & SECURITY OF PAYMENT
- Payment disputes
- Construction company collapses
- Security of payment claims

### ADR
- Notable arbitration or mediation matters

### CORPORATE GOVERNANCE
- Director penalty matters
- Insolvent trading allegations
- Governance breaches

## MARKET INTELLIGENCE
- Industries under stress by practice area
- Regulatory enforcement trends
- Emerging legal risks

## MEDIA ANALYSIS
Key themes from news coverage with business development implications.

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
- ASIC Intelligence
- ACCC Intelligence
- ASX Company News
- Court Cases (AustLII)
- Australian Business News

Note which practice areas have strong vs. weak intelligence coverage and suggest improvements.

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
Sources: Google News, ASIC, ACCC, ASX (via Google), AustLII (FCA/NSWSC/VSC), ABC/SBS/Guardian/Nine News
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

def send_email_briefing(briefing, filename=None):
    """
    Send briefing via email
    """
    try:
        email_to = os.environ.get('EMAIL_TO')
        email_from = os.environ.get('EMAIL_FROM')
        email_password = os.environ.get('EMAIL_PASSWORD')
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp-mail.outlook.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        
        if not all([email_to, email_from, email_password]):
            print("⚠ Email configuration incomplete - skipping email delivery")
            return False
        
        print(f"Sending email to {email_to}...")
        
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = f"Legal Intelligence Briefing - {datetime.now().strftime('%A, %d %B %Y')}"
        
        body = f"""Good morning,

Your Australian Legal Intelligence Briefing for {datetime.now().strftime('%A, %d %B %Y')} is ready.

{'='*70}

{briefing}

{'='*70}

This briefing was automatically generated by your Legal Intelligence Agent.
Practice Areas: Insolvency, Regulatory, Workplace, Litigation, ADR, Construction, Governance
Sources: Google News, ASIC, ACCC, ASX, AustLII, Australian Media

Best regards,
Legal Intelligence Agent
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        if filename and os.path.exists(filename):
            with open(filename, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(filename)}')
                msg.attach(part)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_from, email_password)
            server.send_message(msg)
        
        print(f"✓ Email sent successfully to {email_to}")
        return True
        
    except Exception as e:
        print(f"✗ Error sending email: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AUSTRALIAN LEGAL INTELLIGENCE AGENT")
    print("Enhanced Multi-Source Edition")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    try:
        briefing = generate_briefing()
        filename = save_briefing(briefing)
        email_sent = send_email_briefing(briefing, filename)
        
        print("\n" + "="*70)
        print("BRIEFING CONTENT")
        print("="*70 + "\n")
        print(briefing)
        print("\n" + "="*70)
        
        if email_sent:
            print("\n✓ Agent completed successfully - Email delivered!")
        else:
            print("\n✓ Agent completed - Check artifacts for briefing")
        
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {str(e)}")
        traceback.print_exc()
        exit(1)
