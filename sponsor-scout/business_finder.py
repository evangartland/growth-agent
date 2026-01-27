#!/usr/bin/env python3
"""
Sponsor Scout - Local Business Finder

Finds potential sponsor businesses near a given suburb/postcode using
Google Maps Places API.
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from typing import Optional

import googlemaps
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry

load_dotenv()

# Rate limiting: Google Places API allows 100 requests per second
# We'll be conservative with 10 requests per second
CALLS_PER_SECOND = 10
RATE_LIMIT_PERIOD = 1

# Business categories to search for potential sponsors
BUSINESS_CATEGORIES = [
    "gym",
    "restaurant",
    "cafe",
    "doctor",  # medical centers
    "dentist",
    "physiotherapist",
    "real_estate_agency",
    "accounting",
    "lawyer",
    "car_dealer",
    "sporting_goods_store",
    "supermarket",
]

# Human-readable category names for output
CATEGORY_DISPLAY_NAMES = {
    "gym": "Gym",
    "restaurant": "Restaurant",
    "cafe": "Cafe",
    "doctor": "Medical Center",
    "dentist": "Dental Clinic",
    "physiotherapist": "Physiotherapy",
    "real_estate_agency": "Real Estate Agent",
    "accounting": "Accountant",
    "lawyer": "Law Firm",
    "car_dealer": "Car Dealership",
    "sporting_goods_store": "Sporting Goods Store",
    "supermarket": "Supermarket",
}


class BusinessFinder:
    """Find local businesses using Google Maps Places API."""

    def __init__(self, api_key: str):
        """Initialize with Google Maps API key."""
        self.client = googlemaps.Client(key=api_key)

    def geocode_location(self, location: str) -> Optional[dict]:
        """
        Convert a suburb/postcode to lat/lng coordinates.

        Args:
            location: Suburb name or postcode (e.g., "Bondi NSW" or "2026")

        Returns:
            Dict with 'lat' and 'lng' keys, or None if not found
        """
        try:
            results = self.client.geocode(location + ", Australia")
            if results:
                geometry = results[0]["geometry"]["location"]
                return {"lat": geometry["lat"], "lng": geometry["lng"]}
        except Exception as e:
            print(f"Error geocoding location: {e}")
        return None

    @sleep_and_retry
    @limits(calls=CALLS_PER_SECOND, period=RATE_LIMIT_PERIOD)
    def _rate_limited_places_nearby(self, **kwargs) -> dict:
        """Rate-limited wrapper for places_nearby API call."""
        return self.client.places_nearby(**kwargs)

    @sleep_and_retry
    @limits(calls=CALLS_PER_SECOND, period=RATE_LIMIT_PERIOD)
    def _rate_limited_place_details(self, place_id: str) -> dict:
        """Rate-limited wrapper for place details API call."""
        return self.client.place(
            place_id,
            fields=["name", "formatted_address", "formatted_phone_number",
                    "website", "place_id", "types", "business_status"]
        )

    def search_businesses(
        self,
        location: dict,
        category: str,
        radius: int = 5000
    ) -> list[dict]:
        """
        Search for businesses of a specific category near a location.

        Args:
            location: Dict with 'lat' and 'lng' keys
            category: Google Places type (e.g., 'gym', 'restaurant')
            radius: Search radius in meters (default 5km)

        Returns:
            List of business dictionaries
        """
        businesses = []

        try:
            # Initial search
            response = self._rate_limited_places_nearby(
                location=location,
                radius=radius,
                type=category
            )

            businesses.extend(response.get("results", []))

            # Handle pagination (up to 60 results total)
            while "next_page_token" in response:
                # Google requires a short delay before using next_page_token
                time.sleep(2)
                response = self._rate_limited_places_nearby(
                    location=location,
                    page_token=response["next_page_token"]
                )
                businesses.extend(response.get("results", []))

        except Exception as e:
            print(f"Error searching for {category}: {e}")

        return businesses

    def get_business_details(self, place_id: str) -> Optional[dict]:
        """
        Get detailed information for a specific business.

        Args:
            place_id: Google Places place_id

        Returns:
            Dict with business details or None if not found
        """
        try:
            result = self._rate_limited_place_details(place_id)
            if result and "result" in result:
                place = result["result"]
                # Only include operational businesses
                if place.get("business_status") == "OPERATIONAL":
                    return {
                        "name": place.get("name", ""),
                        "address": place.get("formatted_address", ""),
                        "phone": place.get("formatted_phone_number", ""),
                        "website": place.get("website", ""),
                        "place_id": place.get("place_id", ""),
                    }
        except Exception as e:
            print(f"Error getting details for {place_id}: {e}")
        return None

    def find_sponsors(
        self,
        location_query: str,
        radius: int = 5000,
        categories: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Find potential sponsor businesses near a location.

        Args:
            location_query: Suburb name or postcode
            radius: Search radius in meters (default 5km)
            categories: List of categories to search (default: all)

        Returns:
            List of business dictionaries with details
        """
        # Geocode the location
        print(f"Geocoding location: {location_query}")
        coords = self.geocode_location(location_query)
        if not coords:
            print(f"Could not find location: {location_query}")
            return []

        print(f"Found coordinates: {coords['lat']}, {coords['lng']}")

        # Use specified categories or default to all
        search_categories = categories or BUSINESS_CATEGORIES

        # Collect all unique place_ids across categories
        all_place_ids = {}  # place_id -> category

        for category in search_categories:
            display_name = CATEGORY_DISPLAY_NAMES.get(category, category)
            print(f"Searching for: {display_name}...")

            results = self.search_businesses(coords, category, radius)
            print(f"  Found {len(results)} results")

            for result in results:
                place_id = result.get("place_id")
                if place_id and place_id not in all_place_ids:
                    all_place_ids[place_id] = category

        print(f"\nTotal unique businesses found: {len(all_place_ids)}")
        print("Fetching detailed information...")

        # Fetch details for each unique business
        businesses = []
        for i, (place_id, category) in enumerate(all_place_ids.items(), 1):
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(all_place_ids)}")

            details = self.get_business_details(place_id)
            if details:
                details["category"] = CATEGORY_DISPLAY_NAMES.get(category, category)
                businesses.append(details)

        print(f"Successfully retrieved details for {len(businesses)} businesses")
        return businesses


def save_to_csv(businesses: list[dict], filename: str) -> None:
    """
    Save business data to a CSV file.

    Args:
        businesses: List of business dictionaries
        filename: Output CSV filename
    """
    if not businesses:
        print("No businesses to save")
        return

    fieldnames = ["name", "category", "address", "phone", "website", "place_id"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(businesses)

    print(f"Saved {len(businesses)} businesses to {filename}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Find potential sponsor businesses near a location"
    )
    parser.add_argument(
        "location",
        help="Suburb name or postcode (e.g., 'Bondi NSW' or '2026')"
    )
    parser.add_argument(
        "-r", "--radius",
        type=int,
        default=5000,
        help="Search radius in meters (default: 5000)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output CSV filename (default: sponsors_<location>_<date>.csv)"
    )
    parser.add_argument(
        "-c", "--categories",
        nargs="+",
        choices=BUSINESS_CATEGORIES,
        help="Specific categories to search (default: all)"
    )

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set")
        print("Create a .env file with your API key or set the environment variable")
        sys.exit(1)

    # Create finder and search
    finder = BusinessFinder(api_key)
    businesses = finder.find_sponsors(
        args.location,
        radius=args.radius,
        categories=args.categories
    )

    # Generate output filename if not specified
    if args.output:
        output_file = args.output
    else:
        safe_location = args.location.replace(" ", "_").replace(",", "")
        date_str = datetime.now().strftime("%Y%m%d")
        output_file = f"sponsors_{safe_location}_{date_str}.csv"

    # Save results
    save_to_csv(businesses, output_file)


if __name__ == "__main__":
    main()
