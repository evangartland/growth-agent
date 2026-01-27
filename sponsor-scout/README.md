# Sponsor Scout

Find potential sponsor businesses for sports clubs using Google Maps Places API.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Get a Google Maps API key:
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create a project and enable **Places API** and **Geocoding API**
   - Create an API key

3. Configure your API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your API key
   ```

## Usage

Basic usage - search all categories within 5km:
```bash
python business_finder.py "Bondi NSW"
```

Search with a postcode:
```bash
python business_finder.py "2026"
```

Custom radius (10km):
```bash
python business_finder.py "Richmond VIC" --radius 10000
```

Search specific categories only:
```bash
python business_finder.py "Parramatta NSW" --categories gym restaurant cafe
```

Custom output filename:
```bash
python business_finder.py "Sydney CBD" --output my_sponsors.csv
```

## Business Categories

The tool searches for these business types:
- Gyms
- Restaurants
- Cafes
- Medical Centers
- Dental Clinics
- Physiotherapy
- Real Estate Agents
- Accountants
- Law Firms
- Car Dealerships
- Sporting Goods Stores
- Supermarkets

## Output

Results are saved to a CSV file with these fields:
- `name` - Business name
- `category` - Business type
- `address` - Full address
- `phone` - Phone number
- `website` - Website URL
- `place_id` - Google Places ID (useful for deduplication)

## Rate Limiting

The tool automatically rate-limits API requests to 10 per second to stay within Google's quotas.
