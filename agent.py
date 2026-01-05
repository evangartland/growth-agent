"""
Configuration file for Australian Legal Intelligence Agent
"""

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
```

## 3. `.gitignore` (New File - Important!)
```
# Performance and error logs
source_performance.json
error_log.txt

# Briefing outputs (optional - remove if you want to track them)
briefing_*.txt
briefing.txt

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
