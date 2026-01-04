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
    Fetch recent ASIC insolvency notices from the public website
    """
    notices = []
    try:
        url = "https://insolvencynotices.asic.gov.au/browsesearch-notices/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            page_text = soup.get_text()
            if 'notice' in page_text.lower() or 'insolvency' in page_text.lower():
                notices.append({
                    'status': 'ASIC Insolvency Notices page accessible',
                    'note': 'Page loaded successfully - would need detailed parsing for specific notices',
                    'url': url
                })
            else:
                notices.append({
                    'status': 'Page loaded but structure unknown',
                    'url': url
                })
            
            print(f"✓ ASIC Insolvency page accessed (HTTP {response.status_code})")
        else:
            notices.append({
                'status': f'HTTP {response.status_code}',
                'url': url
            })
            print(f"⚠ ASIC Insolvency returned HTTP {response.status_code}")
            
    except Exception as e:
        print(f"✗ ASIC Insolvency error: {str(e)[:100]}")
        notices = [{'error': str(e)[:200], 'source': 'ASIC Insolvency'}]
    
    return notices if notices else [{'note': 'No data retrieved'}]

def fetch_asic_company_announcements():
    """
    Fetch ASIC media releases
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
            
            links = soup.find_all('a', limit=20)
            
            for link in links:
                text = link.get_text(strip=True)
                href = link.get('href', '')
                
                if 'media-release' in href.lower() or len(text) > 30:
                    if any(keyword in text.lower() for keyword in ['release', 'asic', '202']):
                        announcements.append({
                            'title': text[:200],
                            'source': 'ASIC'
                        })
            
            if announcements:
                print(f"✓ Found {len(announcements)} ASIC items")
            else:
                announcements = [{'status': 'ASIC page accessed', 'url': url}]
                print(f"✓ ASIC page accessed (HTTP {response.status_code})")
        else:
            announcements = [{'status': f'HTTP {response.status_code}', 'url': url}]
            print(f"⚠ ASIC returned HTTP {response.status_code}")
        
    except Exception as e:
        print(f"✗ ASIC announcements error: {str(e)[:100]}")
        announcements = [{'error': str(e)[:200]}]
    
    return announcements if announcements else [{'note': 'No data retrieved'}]

def fetch_federal_court_notices():
    """
    Fetch Federal Court info
    """
    filings = []
    
    try:
        url = "https://www.fedcourt.gov.au/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            filings = [{'status': 'Federal Court website accessible', 'url': url}]
            print(f"✓ Federal Court page accessed")
        else:
            filings = [{'status': f'HTTP {response.status_code}', 'url': url}]
            print(f"⚠ Federal Court returned HTTP {response.status_code}")
        
    except Exception as e:
        print(f"✗ Federal Court error: {str(e)[:100]}")
        filings = [{'error': str(e)[:200]}]
    
    return filings if filings else [{'note': 'No data retrieved'}]

def fetch_accc_enforcement():
    """
    Monitor ACCC enforcement actions
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
            
            links = soup.find_all('a', limit=30)
            
            for link in links:
                text = link.get_text(strip=True)
                if len(text) > 20:
                    if any(keyword in text.lower() for keyword in ['court', 'penalty', 'action', 'proceeding']):
                        enforcement.append({
                            'title': text[:200],
                            'source': 'ACCC'
                        })
            
            if enforcement:
                print(f"✓ Found {len(enforcement)} ACCC enforcement items")
            else:
                enforcement = [{'status': 'ACCC page accessed', 'url': url}]
                print(f"✓ ACCC page accessed")
        else:
            enforcement = [{'status': f'HTTP {response.status_code}', 'url': url}]
            print(f"⚠ ACCC returned HTTP {response.status_code}")
        
    except Exception as e:
        print(f"✗ ACCC error: {str(e)[:100]}")
        enforcement = [{'error': str(e)[:200]}]
    
    return enforcement if enforcement else [{'note': 'No data retrieved'}]

def fetch_asx_announcements():
    """
    ASX announcements - limited free access
    """
    announcements = []
    
    try:
        announcements = [{
            'note': 'ASX price-sensitive announcements require market data subscription',
            'recommendation': 'Consider: IRESS, Morningstar, or direct ASX data feed',
            'free_alternative': 'Monitor specific company pages or set up Google Finance alerts'
        }]
        print("ℹ ASX data requires subscription")
        
    except Exception as e:
        print(f"✗ ASX error: {str(e)[:100]}")
        announcements = [{'error': str(e)[:200]}]
    
    return announcements

def fetch_austlii_cases():
    """
    Search AustLII for recent cases
    """
    cases = []
    
    try:
        url = "http://www.austlii.edu.au/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            cases = [{
                'status': 'AustLII accessible',
                'note': 'Free legal database - configure specific court searches',
                'databases': ['FCA', 'NSWSC', 'VSC', 'QSC'],
                'url': url
            }]
            print(f"✓ AustLII accessed")
        else:
            cases = [{'status': f'HTTP {response.status_code}', 'url': url}]
            print(f"⚠ AustLII returned HTTP {response.status_code}")
        
    except Exception as e:
        print(f"✗ AustLII error: {str(e)[:100]}")
        cases = [{'error': str(e)[:200]}]
    
    return cases if cases else [{'note': 'No data retrieved'}]

def fetch_abc_news_business():
    """
    Fetch ABC News Business
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
            
            links = soup.find_all('a', limit=30)
            
            for link in links:
                text = link.get_text(strip=True)
                if len(text) > 20:
                    if any(keyword in text.lower() for keyword in 
                        ['company', 'court', 'asic', 'accc', 'administration', 'bankruptcy', 'lawsuit']):
                        news.append({
                            'headline': text[:200],
                            'source': 'ABC News'
                        })
            
            if news:
                print(f"✓ Found {len(news)} ABC news items")
            else:
                print(f"✓ ABC News accessed (no matching items)")
        
    except Exception as e:
        print(f"⚠ ABC News error: {str(e)[:100]}")
    
    return news

def generate_briefing():
    """
    Collect all data and generate briefing using Claude
    """
    print("\n" + "="*70)
    print("COLLECTING AUSTRALIAN LEGAL INTELLIGENCE DATA")
    print("="*70 + "\n")
    
    try:
        print("Fetching ASIC insolvency notices...")
        asic_insolvency = fetch_asic_insolvency_notices()
        time.sleep(1)
        
        print("Fetching ASIC announcements...")
        asic_announcements = fetch_asic_company_announcements()
        time.sleep
