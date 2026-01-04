import anthropic
import requests
from datetime import datetime, timedelta
import os
import json
from bs4 import BeautifulSoup
import time

def fetch_asic_insolvency_notices():
    """
    Fetch recent ASIC insolvency notices
    ASIC publishes these at: https://insolvencynotices.asic.gov.au/
    """
    notices = []
    try:
        # ASIC Insolvency Notices search
        base_url = "https://insolvencynotices.asic.gov.au/browsesearch-notices/notice-search"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Search for notices from last 24 hours
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
        today = datetime.now().strftime('%d/%m/%Y')
        
        params = {
            'startDate': yesterday,
            'endDate': today
        }
        
        response = requests.get(base_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            notice_items = soup.find_all('div', class_='notice-item')[:20]
            
            for item in notice_items:
                notices.append({
                    'company': item.get_text(strip=True) if item else 'Unknown',
                    'source': 'ASIC Insolvency Notices'
                })
        
        if not notices:
            notices = [{
                'note': 'ASIC Insolvency Notices require proper authentication/scraping setup',
                'action': 'Configure proper API access or web scraping',
                'source': 'ASIC Insolvency Notices'
            }]
            
    except Exception as e:
        notices = [{
            'error': str(e),
            'note': 'Check ASIC website structure or implement API access',
            'source': 'ASIC Insolvency Notices'
        }]
    
    return notices

def fetch_asic_company_changes():
    """
    Monitor ASIC registers for significant company changes
    This would typically require ASIC Connect API access
    """
    changes = []
    
    try:
        changes = [{
            'type': 'Director Appointments',
            'note': 'Requires ASIC Connect API credentials',
            'data_points': [
                'New director appointments in large companies',
                'Director resignations',
                'Changes in shareholding structure'
            ]
        }, {
            'type': 'External Administration',
            'note': 'Monitor for companies entering administration',
            'data_points': [
                'Voluntary administration appointments',
                'Receivership appointments',
                'Liquidation notices'
            ]
        }, {
            'type': 'Company Status Changes',
            'note': 'Track deregistrations and status changes',
            'data_points': [
                'Companies under external administration',
                'Deregistered companies',
                'Companies with changed status'
            ]
        }]
        
    except Exception as e:
        changes = [{
            'error': str(e),
            'source': 'ASIC Company Registers'
        }]
    
    return changes

def fetch_federal_court_notices():
    """
    Fetch Federal Court of Australia filings and notices
    """
    filings = []
    
    try:
        url = "https://www.fedcourt.gov.au/services/access-to-files-and-transcripts/online-files"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            filings = [{
                'source': 'Federal Court of Australia',
                'note': 'Configure specific matter type filters',
                'focus_areas': [
                    'Corporations Act applications',
                    'Class actions',
                    'Regulatory proceedings (ASIC, ACCC)',
                    'Insolvency matters'
                ]
            }]
        
    except Exception as e:
        filings = [{
            'error': str(e),
            'source': 'Federal Court'
        }]
    
    return filings

def fetch_accc_enforcement():
    """
    Monitor ACCC enforcement actions and media releases
    """
    enforcement = []
    
    try:
        url = "https://www.accc.gov.au/media-release"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            releases = soup.find_all('article', limit=10)
            
            for release in releases:
                title_elem = release.find('h3') or release.find('h2') or release.find('a')
                if title_elem:
                    enforcement.append({
                        'title': title_elem.get_text(strip=True),
                        'source': 'ACCC'
                    })
        
        if not enforcement:
            enforcement = [{
                'note': 'ACCC media releases - configure scraping',
                'source': 'ACCC'
            }]
            
    except Exception as e:
        enforcement = [{
            'error': str(e),
            'source': 'ACCC'
        }]
    
    return enforcement

def fetch_asx_announcements():
    """
    Monitor ASX announcements for companies in administration, 
    class actions, regulatory issues
    """
    announcements = []
    
    try:
        announcements = [{
            'note': 'ASX Market Announcements - Price Sensitive',
            'focus': [
                'Companies announcing regulatory investigations',
                'Class action litigation announcements',
                'Administration/insolvency announcements',
                'Director changes in listed companies'
            ],
            'source': 'ASX'
        }]
        
    except Exception as e:
        announcements = [{
            'error': str(e),
            'source': 'ASX'
        }]
    
    return announcements

def fetch_austlii_cases():
    """
    Search AustLII for recent significant cases
    """
    cases = []
    
    try:
        databases = [
            'FCA (Federal Court)',
            'NSWSC (NSW Supreme Court)',
            'VSC (Victorian Supreme Court)',
            'QSC (Queensland Supreme Court)'
        ]
        
        cases = [{
            'databases': databases,
            'note': 'Configure AustLII scraping for recent judgments',
            'focus': 'Corporations law, insolvency, regulatory matters',
            'source': 'AustLII'
        }]
        
    except Exception as e:
        cases = [{
            'error': str(e),
            'source': 'AustLII'
        }]
    
    return cases

def generate_briefing():
    """
    Collect all data and generate briefing using Claude
    """
    print("Collecting Australian legal intelligence data...")
    
    # Collect data from all sources
    asic_insolvency = fetch_asic_insolvency_notices()
    asic_changes = fetch_asic_company_changes()
    federal_court = fetch_federal_court_notices()
    accc_enforcement = fetch_accc_enforcement()
    asx_announcements = fetch_asx_announcements()
    austlii_cases = fetch_austlii_cases()
    
    # Format data for Claude
    data_summary = f"""
=== ASIC INSOLVENCY NOTICES ===
{json.dumps(asic_insolvency, indent=2)}

=== ASIC COMPANY REGISTER CHANGES ===
{json.dumps(asic_changes, indent=2)}

=== FEDERAL COURT FILINGS ===
{json.dumps(federal_court, indent=2)}

=== ACCC ENFORCEMENT ACTIONS ===
{json.dumps(accc_enforcement, indent=2)}

=== ASX ANNOUNCEMENTS ===
{json.dumps(asx_announcements, indent=2)}

=== AUSTLII RECENT CASES ===
{json.dumps(austlii_cases, indent=2)}
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
        print(f"API Key found (starts with: {api_key[:15]}...)")
        print(f"API Key length: {len(api_key)}")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"""You are a legal intelligence analyst for an Australian commercial law firm specializing in disputes, insolvency, and regulatory matters.

Analyze this data from {datetime.now().strftime('%A, %d %B %Y')} (Australian sources):

{data_summary}

Provide a concise morning briefing with:

## EXECUTIVE SUMMARY
[2-3 sentences highlighting the most significant developments for business development opportunities]

## HIGH-PRIORITY OPPORTUNITIES
[Ranked list of specific matters worth pursuing - focus on:
- Companies entering external administration
- Significant director changes suggesting distress
- ACCC enforcement actions with class action potential
- Federal Court matters indicating regulatory/commercial disputes
- ASX announcements revealing litigation or regulatory exposure]

## EMERGING TRENDS
[Patterns across industries, regulators, insolvency types, or dispute categories]

## MARKET INTELLIGENCE
[Insights about:
- Industries under stress
- Regulatory focus areas
- Competitor activity (other law firms)]

## RECOMMENDED ACTIONS
[Specific next steps for business development team:
- Companies to contact
- Matters to monitor
- Conflicts to check]

Be specific about company names, ACNs, amounts, and jurisdictions when available. Flag matters that may require immediate attention.

Note: Some data sources may be placeholder data requiring configuration - focus analysis on available concrete data and provide strategic recommendations for improving data collection."""
            }]
        )
        
        briefing_text = message.content[0].text
        print("Briefing generated successfully!")
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
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Error: {str(e)}

You've hit the rate limit for the Anthropic API.

Wait a few minutes and try again.

Data collected:
{data_summary}
"""
        print(error_message)
        return error_message
        
    except Exception as e:
        error_message = f"""
ERROR GENERATING BRIEFING
========================
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Error: {str(e)}
Error Type: {type(e).__name__}

Data collected:
{data_summary}

Please check:
1. ANTHROPIC_API_KEY is set correctly in GitHub Secrets
2. API key has sufficient credits
3. Network connectivity
4. API status at: https://status.anthropic.com/
"""
        print(error_message)
        return error_message

def save_briefing(briefing):
    """
    Save briefing to file for GitHub Actions artifacts
    """
    filename = f"briefing_{datetime.now().strftime('%Y%m%d')}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"AUSTRALIAN LEGAL INTELLIGENCE BRIEFING\n")
        f.write(f"Generated: {datetime.now().strftime('%A, %d %B %Y at %H:%M AEST')}\n")
        f.write("="*70 + "\n\n")
        f.write(briefing)
    
    # Also save as briefing.txt for consistent artifact name
    with open('briefing.txt', 'w', encoding='utf-8') as f:
        f.write(f"AUSTRALIAN LEGAL INTELLIGENCE BRIEFING\n")
        f.write(f"Generated: {datetime.now().strftime('%A, %d %B %Y at %H:%M AEST')}\n")
        f.write("="*70 + "\n\n")
        f.write(briefing)
    
    print(f"Briefing saved to {filename} and briefing.txt")
    return filename

def send_to_slack(briefing):
    """
    Optional: Send briefing to Slack
    """
    webhook_url = os.environ.get('SLACK_WEBHOOK')
    
    if not webhook_url:
        print("No Slack webhook configured - skipping Slack notification")
        return
    
    try:
        # Slack has a 3000 character limit for text, so truncate if needed
        truncated = briefing[:2900] + "..." if len(briefing) > 3000 else briefing
        
        payload = {
            "text": f"*Australian Legal Intelligence Briefing - {datetime.now().strftime('%d %b %Y')}*\n\n{truncated}",
            "mrkdwn": True
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("Briefing sent to Slack successfully")
        else:
            print(f"Failed to send to Slack: {response.status_code}")
            
    except Exception as e:
        print(f"Error sending to Slack: {str(e)}")

if __name__ == "__main__":
    print("Starting Australian Legal Intelligence Agent...")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for API key before proceeding
    if 'ANTHROPIC_API_KEY' in os.environ:
        api_key = os.environ['ANTHROPIC_API_KEY']
        print(f"✓ API Key found (starts with: {api_key[:15]}...)")
    else:
        print("✗ WARNING: ANTHROPIC_API_KEY not found in environment variables")
    
    # Generate the briefing
    briefing = generate_briefing()
    
    # Save to file
    filename = save_briefing(briefing)
    
    # Print to console (will appear in GitHub Actions logs)
    print("\n" + "="*70)
    print("BRIEFING CONTENT")
    print("="*70)
    print(briefing)
    print("="*70 + "\n")
    
    # Optional: Send to Slack
    send_to_slack(briefing)
    
    print("Agent completed successfully!")
