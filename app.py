"""
Flask API Server for Corporate Law Landing Page
Handles form submissions and serves the landing page
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from form_handler import SubscriptionManager
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Initialize subscription manager
subscription_manager = SubscriptionManager()


@app.route('/')
def index():
    """Serve the landing page"""
    return send_file('landing_page.html')


@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    """
    Handle subscription form submissions

    Expected JSON payload:
    {
        "practiceArea": "string",
        "jurisdiction": "string",
        "companies": "string (comma-separated)",
        "email": "string"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['practiceArea', 'jurisdiction', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Validate email format
        email = data['email']
        if '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400

        # Add subscription
        success = subscription_manager.add_subscription(data)

        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully subscribed to legal intelligence briefings'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Email already subscribed or database error'
            }), 409

    except Exception as e:
        app.logger.error(f"Error processing subscription: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    """
    Get all active subscriptions (admin endpoint - should be protected in production)
    """
    try:
        jurisdiction = request.args.get('jurisdiction')
        practice_area = request.args.get('practiceArea')
        company = request.args.get('company')

        if jurisdiction:
            subscriptions = subscription_manager.get_subscriptions_by_jurisdiction(jurisdiction)
        elif practice_area:
            subscriptions = subscription_manager.get_subscriptions_by_practice_area(practice_area)
        elif company:
            subscriptions = subscription_manager.get_subscriptions_for_company(company)
        else:
            subscriptions = subscription_manager.get_all_subscriptions()

        return jsonify({
            'success': True,
            'count': len(subscriptions),
            'subscriptions': subscriptions
        }), 200

    except Exception as e:
        app.logger.error(f"Error fetching subscriptions: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/unsubscribe', methods=['POST'])
def unsubscribe():
    """
    Handle unsubscribe requests

    Expected JSON payload:
    {
        "email": "string"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        success = subscription_manager.unsubscribe(email)

        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully unsubscribed'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Email not found or database error'
            }), 404

    except Exception as e:
        app.logger.error(f"Error processing unsubscribe: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/export-emails', methods=['GET'])
def export_emails():
    """
    Export email addresses for mailing list (admin endpoint)
    """
    try:
        jurisdiction = request.args.get('jurisdiction')
        emails = subscription_manager.export_emails(jurisdiction)

        return jsonify({
            'success': True,
            'count': len(emails),
            'emails': emails
        }), 200

    except Exception as e:
        app.logger.error(f"Error exporting emails: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Corporate Law Intelligence API'
    }), 200


if __name__ == '__main__':
    # Development server
    print("=" * 60)
    print("Corporate Law Intelligence Landing Page")
    print("=" * 60)
    print("\nStarting Flask server...")
    print("Landing page: http://localhost:5000")
    print("API endpoint: http://localhost:5000/api/subscribe")
    print("Admin panel: http://localhost:5000/api/subscriptions")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60)

    # Run in debug mode for development
    app.run(host='0.0.0.0', port=5000, debug=True)
