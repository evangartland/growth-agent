# SponsorScout UK

Find potential sponsor businesses for UK sports clubs using Google Maps Places API, with optional Companies House verification.

## Features

- **UK Postcode Support**: Validates and geocodes UK postcodes (e.g., SW1A 1AA, M1 1AE)
- **UK-Focused Categories**: Business types relevant to sports club sponsorship
- **Companies House Integration**: Verify businesses are registered and active (optional)
- **Rate Limiting**: Built-in protection against API quota limits
- **CSV Export**: Easy-to-use output for CRM import

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

#### Google Maps API Key (Required)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a project (or select existing)
3. Enable **Places API** and **Geocoding API**
4. Create an API key and add it to `.env`

#### Companies House API Key (Optional)

1. Register at [Companies House Developer Hub](https://developer.company-information.service.gov.uk/)
2. Create an application
3. Copy the API key to `.env`

## Usage

### Basic Search

Search for all business categories within 5km of a postcode:

```bash
python sponsor_scout.py "SW1A 1AA"
```

### With Postcode Formats

Both formats work:

```bash
python sponsor_scout.py SW1A1AA    # No space
python sponsor_scout.py "SW1A 1AA" # With space (use quotes)
```

### Custom Radius

Search within 10km:

```bash
python sponsor_scout.py "M1 1AE" --radius 10000
```

### With Companies House Verification

Verify businesses are registered companies:

```bash
python sponsor_scout.py "E14 5AB" --verify
```

### Specific Categories Only

Search only pubs and restaurants:

```bash
python sponsor_scout.py "N1 9GU" --categories pub restaurant
```

### Include Supermarket Chains

Include Tesco, Sainsbury's, and Co-op:

```bash
python sponsor_scout.py "SE1 7PB" --include-chains
```

### List Available Categories

```bash
python sponsor_scout.py --list-categories
```

## Business Categories

| Category | Description |
|----------|-------------|
| `pub` | Pubs and bars |
| `restaurant` | Restaurants |
| `estate_agent` | Estate agents |
| `solicitor` | Solicitors and law firms |
| `accountant` | Accountancy firms |
| `insurance_broker` | Insurance brokers |
| `recruitment_agency` | Recruitment agencies |
| `private_healthcare` | Private healthcare providers |
| `dental_practice` | Dental practices |
| `physiotherapy` | Physiotherapy clinics |
| `sports_injury_clinic` | Sports injury clinics |
| `gym` | Gyms and fitness centres |
| `leisure_centre` | Leisure centres |
| `construction` | Construction firms |
| `builder` | Building firms |
| `supermarket` | Local supermarkets |
| `tesco` | Tesco stores (use --include-chains) |
| `sainsburys` | Sainsbury's stores (use --include-chains) |
| `coop` | Co-op stores (use --include-chains) |
| `car_dealership` | Car dealerships |
| `garage` | Car garages and repair shops |
| `sports_shop` | Sports shops |
| `independent_retailer` | Independent retailers |

## Output

Results are saved to CSV with the following fields:

| Field | Description |
|-------|-------------|
| `name` | Business name |
| `category` | Business type |
| `address` | Full address |
| `phone` | Phone number |
| `website` | Website URL |
| `place_id` | Google Places ID |

With `--verify` flag, additional fields:

| Field | Description |
|-------|-------------|
| `ch_company_number` | Companies House number |
| `ch_company_status` | Company status (active, dissolved, etc.) |
| `ch_verified` | True if active registered company |

## Rate Limiting

- **Google Maps API**: 10 requests/second (conservative limit)
- **Companies House API**: 2 requests/second

## Project Structure

```
sponsorscout-uk/
├── sponsor_scout.py      # Main entry point (recommended)
├── business_finder.py    # Google Maps integration
├── companies_house.py    # Companies House integration
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
└── README.md             # This file
```

## Standalone Usage

### Business Finder Only

```bash
python business_finder.py "SW1A 1AA" --radius 5000
```

### Companies House Lookup

```bash
python companies_house.py "Example Ltd"
```

## Notes

- **Postcode Validation**: Only valid UK postcode formats are accepted
- **Companies House Matching**: Not all businesses are registered (sole traders, partnerships)
- **API Costs**: Check Google Cloud pricing for Places API usage
- **Data Freshness**: Google Maps data may not always be current
