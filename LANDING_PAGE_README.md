# Corporate Law Intelligence Landing Page

A professional landing page that allows users to sign up for tailored legal intelligence briefings based on their practice areas, jurisdiction, and focus companies.

## Features

### User Signup Form
- **Practice Area Selection**: Comprehensive dropdown with 60+ corporate law practice areas including:
  - Corporate & Commercial (M&A, Corporate Governance, Securities, etc.)
  - Litigation & Dispute Resolution
  - Insolvency & Restructuring
  - Regulatory & Compliance
  - Banking & Finance
  - Employment & Labor
  - Tax
  - Intellectual Property
  - Real Estate & Construction
  - Energy & Resources
  - Technology & Innovation
  - Healthcare & Life Sciences

- **Jurisdiction Selection**: Australia, United Kingdom, United States

- **Focus Companies**: Free text field for comma-separated company names that users want to monitor

- **Email Address**: User's email for receiving briefings

### Backend Features
- **Subscription Management**: Store and manage user subscriptions in JSON format
- **API Endpoints**: RESTful API for subscription handling
- **Data Export**: Export email lists by jurisdiction or practice area
- **Duplicate Prevention**: Prevents multiple subscriptions with same email

## File Structure

```
growth-agent/
├── landing_page.html      # Frontend landing page with form
├── app.py                 # Flask API server
├── form_handler.py        # Subscription management logic
├── subscriptions.json     # User subscription data (created automatically)
└── requirements.txt       # Python dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- Flask-CORS (cross-origin resource sharing)
- All existing dependencies (anthropic, requests, beautifulsoup4, etc.)

### 2. Run the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 3. Access the Landing Page

Open your browser and navigate to:
```
http://localhost:5000
```

## API Endpoints

### POST /api/subscribe
Subscribe a user to legal intelligence briefings.

**Request Body:**
```json
{
  "practiceArea": "Insolvency & Bankruptcy",
  "jurisdiction": "Australia",
  "companies": "Macquarie Bank, Commonwealth Bank, BHP",
  "email": "lawyer@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully subscribed to legal intelligence briefings"
}
```

### GET /api/subscriptions
Get all active subscriptions (admin endpoint).

**Query Parameters:**
- `jurisdiction`: Filter by jurisdiction (optional)
- `practiceArea`: Filter by practice area (optional)
- `company`: Filter by company name (optional)

**Response:**
```json
{
  "success": true,
  "count": 5,
  "subscriptions": [
    {
      "email": "lawyer@example.com",
      "practiceArea": "Insolvency & Bankruptcy",
      "jurisdiction": "Australia",
      "companies": ["Macquarie Bank", "Commonwealth Bank"],
      "subscribedAt": "2026-01-15T10:30:00",
      "active": true
    }
  ]
}
```

### POST /api/unsubscribe
Unsubscribe a user.

**Request Body:**
```json
{
  "email": "lawyer@example.com"
}
```

### GET /api/export-emails
Export email addresses for mailing list.

**Query Parameters:**
- `jurisdiction`: Filter by jurisdiction (optional)

**Response:**
```json
{
  "success": true,
  "count": 3,
  "emails": ["lawyer1@example.com", "lawyer2@example.com", "lawyer3@example.com"]
}
```

### GET /health
Health check endpoint.

## Using the Subscription Manager

The `form_handler.py` module provides a `SubscriptionManager` class for programmatic access:

```python
from form_handler import SubscriptionManager

manager = SubscriptionManager()

# Add a subscription
manager.add_subscription({
    'email': 'lawyer@example.com',
    'practiceArea': 'Insolvency & Bankruptcy',
    'jurisdiction': 'Australia',
    'companies': 'BHP, Rio Tinto'
})

# Get all subscriptions
subs = manager.get_all_subscriptions()

# Filter by jurisdiction
aus_subs = manager.get_subscriptions_by_jurisdiction('Australia')

# Filter by practice area
insolvency_subs = manager.get_subscriptions_by_practice_area('Insolvency & Bankruptcy')

# Find who's watching a specific company
watchers = manager.get_subscriptions_for_company('BHP')

# Export emails for mailing list
emails = manager.export_emails('Australia')
```

## Integration with Existing Agent

The landing page integrates with the existing `agent.py` legal intelligence system. To send briefings to subscribers:

```python
from form_handler import SubscriptionManager
from agent import generate_briefing, send_email

# Get all Australian subscribers interested in Insolvency
manager = SubscriptionManager()
subs = manager.get_subscriptions_by_jurisdiction('Australia')
insolvency_subs = [s for s in subs if 'Insolvency' in s['practiceArea']]

# Generate briefing
briefing = generate_briefing()

# Send to each subscriber
for sub in insolvency_subs:
    send_email(briefing, sub['email'])
```

## Customization

### Adding Practice Areas
Edit `landing_page.html` and add new options within the appropriate `<optgroup>`:

```html
<optgroup label="Your Category">
    <option value="New Practice Area">New Practice Area</option>
</optgroup>
```

### Adding Jurisdictions
Edit the jurisdiction dropdown in `landing_page.html`:

```html
<select id="jurisdiction" name="jurisdiction" required>
    <option value="">Select jurisdiction...</option>
    <option value="Australia">Australia</option>
    <option value="United Kingdom">United Kingdom</option>
    <option value="United States">United States</option>
    <option value="Canada">Canada</option>  <!-- New jurisdiction -->
</select>
```

### Styling
All styles are contained within the `<style>` tag in `landing_page.html`. Modify the CSS variables and classes to match your brand.

## Production Deployment

### Security Recommendations

1. **Add Authentication**: Protect admin endpoints (`/api/subscriptions`, `/api/export-emails`)
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Email Verification**: Add email verification before activating subscriptions
4. **HTTPS**: Always use HTTPS in production
5. **Database**: Replace JSON file storage with a proper database (PostgreSQL, MongoDB)
6. **Environment Variables**: Store sensitive configuration in environment variables

### Deployment Options

**Option 1: Deploy with existing agent on cloud**
- Deploy Flask app to cloud provider (AWS, Azure, GCP)
- Use cloud database for subscriptions
- Schedule agent.py to run daily and email subscribers

**Option 2: Use form submission service**
- Point form to Formspree, Netlify Forms, or Google Forms
- Process submissions via webhook

**Option 3: Serverless**
- Deploy as AWS Lambda + API Gateway
- Store subscriptions in DynamoDB
- Trigger agent via EventBridge schedule

## Data Schema

### Subscription Object
```json
{
  "email": "string (unique)",
  "practiceArea": "string",
  "jurisdiction": "string",
  "companies": ["array", "of", "strings"],
  "subscribedAt": "ISO 8601 datetime",
  "active": "boolean",
  "unsubscribedAt": "ISO 8601 datetime (optional)"
}
```

## Testing

### Manual Testing
1. Start the server: `python app.py`
2. Open `http://localhost:5000` in browser
3. Fill out the form and submit
4. Check `subscriptions.json` file for saved data
5. Test API endpoints with curl or Postman

### Automated Testing
```bash
# Test health endpoint
curl http://localhost:5000/health

# Test subscription
curl -X POST http://localhost:5000/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "practiceArea": "Insolvency & Bankruptcy",
    "jurisdiction": "Australia",
    "companies": "BHP, Rio Tinto",
    "email": "test@example.com"
  }'

# Get subscriptions
curl http://localhost:5000/api/subscriptions

# Export emails
curl http://localhost:5000/api/export-emails?jurisdiction=Australia
```

## Support

For issues or questions, please check:
- Form validation errors appear below each field
- Server logs in terminal for debugging
- Browser console for frontend errors
- `subscriptions.json` for data persistence

## License

This landing page is part of the Australian Legal Intelligence Agent project.
