"""
Form Handler for Corporate Law Landing Page
Saves user subscriptions to a JSON file for processing
"""

import json
import os
from datetime import datetime
from typing import Dict, List


class SubscriptionManager:
    """Manages user subscriptions to legal intelligence briefings"""

    def __init__(self, data_file: str = 'subscriptions.json'):
        self.data_file = data_file
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create subscriptions file if it doesn't exist"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)

    def add_subscription(self, data: Dict) -> bool:
        """
        Add a new subscription

        Args:
            data: Dictionary containing:
                - practiceArea: str
                - jurisdiction: str
                - companies: str (comma-separated)
                - email: str

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load existing subscriptions
            subscriptions = self.get_all_subscriptions()

            # Check if email already exists
            if any(sub['email'] == data['email'] for sub in subscriptions):
                print(f"Email {data['email']} already subscribed")
                return False

            # Add timestamp and parse companies
            subscription = {
                'email': data['email'],
                'practiceArea': data['practiceArea'],
                'jurisdiction': data['jurisdiction'],
                'companies': [c.strip() for c in data.get('companies', '').split(',') if c.strip()],
                'subscribedAt': datetime.now().isoformat(),
                'active': True
            }

            # Add to list
            subscriptions.append(subscription)

            # Save
            with open(self.data_file, 'w') as f:
                json.dump(subscriptions, f, indent=2)

            print(f"✓ Added subscription for {data['email']}")
            return True

        except Exception as e:
            print(f"✗ Error adding subscription: {e}")
            return False

    def get_all_subscriptions(self) -> List[Dict]:
        """Get all active subscriptions"""
        try:
            with open(self.data_file, 'r') as f:
                subscriptions = json.load(f)
            return [sub for sub in subscriptions if sub.get('active', True)]
        except Exception as e:
            print(f"Error reading subscriptions: {e}")
            return []

    def get_subscriptions_by_jurisdiction(self, jurisdiction: str) -> List[Dict]:
        """Get subscriptions for a specific jurisdiction"""
        all_subs = self.get_all_subscriptions()
        return [sub for sub in all_subs if sub['jurisdiction'] == jurisdiction]

    def get_subscriptions_by_practice_area(self, practice_area: str) -> List[Dict]:
        """Get subscriptions for a specific practice area"""
        all_subs = self.get_all_subscriptions()
        return [sub for sub in all_subs if sub['practiceArea'] == practice_area]

    def get_subscriptions_for_company(self, company_name: str) -> List[Dict]:
        """Get all subscriptions that are watching a specific company"""
        all_subs = self.get_all_subscriptions()
        return [
            sub for sub in all_subs
            if any(company_name.lower() in c.lower() for c in sub.get('companies', []))
        ]

    def unsubscribe(self, email: str) -> bool:
        """Mark a subscription as inactive"""
        try:
            subscriptions = self.get_all_subscriptions()

            for sub in subscriptions:
                if sub['email'] == email:
                    sub['active'] = False
                    sub['unsubscribedAt'] = datetime.now().isoformat()

            with open(self.data_file, 'w') as f:
                json.dump(subscriptions, f, indent=2)

            print(f"✓ Unsubscribed {email}")
            return True

        except Exception as e:
            print(f"✗ Error unsubscribing: {e}")
            return False

    def export_emails(self, jurisdiction: str = None) -> List[str]:
        """Export email addresses for mailing list"""
        if jurisdiction:
            subs = self.get_subscriptions_by_jurisdiction(jurisdiction)
        else:
            subs = self.get_all_subscriptions()

        return [sub['email'] for sub in subs]


# Example usage
if __name__ == "__main__":
    manager = SubscriptionManager()

    # Example: Add a subscription
    example_data = {
        'email': 'lawyer@example.com',
        'practiceArea': 'Insolvency & Bankruptcy',
        'jurisdiction': 'Australia',
        'companies': 'Macquarie Bank, Commonwealth Bank, BHP'
    }

    manager.add_subscription(example_data)

    # Display all subscriptions
    print("\nAll Subscriptions:")
    for sub in manager.get_all_subscriptions():
        print(f"  - {sub['email']} | {sub['jurisdiction']} | {sub['practiceArea']}")
        if sub.get('companies'):
            print(f"    Watching: {', '.join(sub['companies'])}")

    # Export Australia emails
    print("\nAustralian subscribers:")
    aus_emails = manager.export_emails('Australia')
    for email in aus_emails:
        print(f"  - {email}")
