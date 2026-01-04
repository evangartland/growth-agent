"""
Configuration file for Australian Legal Intelligence Agent

Add your specific configurations here:
- ASIC Connect API credentials
- Specific company ACNs to monitor
- Industry focus areas
- Excluded companies (conflicts)
"""

# Industries to monitor closely
PRIORITY_INDUSTRIES = [
    'Construction',
    'Retail',
    'Financial Services',
    'Mining',
    'Technology',
    'Healthcare'
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
    'winding up'
]

# Your firm's conflict check - companies to exclude
EXCLUDED_COMPANIES = [
    # Add ACNs or company names of existing clients
]
