#!/usr/bin/env python3
"""
SponsorScout UK - Local Business Finder

Finds potential sponsor businesses near a given UK postcode using
Google Maps Places API. Optimised for UK sports clubs seeking
local sponsorship opportunities.
"""

import argparse
import csv
import os
import re
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

# UK postcode regex pattern
# Matches formats like: SW1A 1AA, W1A 0AX, M1 1AE, B33 8TH, CR2 6XH, DN55 1PT
UK_POSTCODE_PATTERN = re.compile(
    r"^([A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})$",
    re.IGNORECASE
)

# UK-specific business categories for sponsor prospecting
# Maps our category names to Google Places types
BUSINESS_CATEGORIES = {
    # Hospitality
    "pub": {"type": "bar", "keyword": "pub"},
    "restaurant": {"type": "restaurant", "keyword": None},

    # Professional services
    "estate_agent": {"type": "real_estate_agency", "keyword": "estate agent"},
    "solicitor": {"type": "lawyer", "keyword": "solicitor"},
    "accountant": {"type": "accounting", "keyword": None},
    "insurance_broker": {"type": None, "keyword": "insurance broker"},
    "recruitment_agency": {"type": "employment_agency", "keyword": "recruitment"},

    # Healthcare
    "private_healthcare": {"type": "doctor", "keyword": "private"},
    "dental_practice": {"type": "dentist", "keyword": None},
    "physiotherapy": {"type": "physiotherapist", "keyword": None},
    "sports_injury_clinic": {"type": "physiotherapist", "keyword": "sports injury"},

    # Fitness and leisure
    "gym": {"type": "gym", "keyword": None},
    "leisure_centre": {"type": "gym", "keyword": "leisure centre"},

    # Construction and trades
    "construction": {"type": "general_contractor", "keyword": "construction"},
    "builder": {"type": "general_contractor", "keyword": "builder"},

    # Retail
    "supermarket": {"type": "supermarket", "keyword": None},
    "tesco": {"type": "supermarket", "keyword": "Tesco"},
    "sainsburys": {"type": "supermarket", "keyword": "Sainsbury's"},
    "coop": {"type": "supermarket", "keyword": "Co-op"},

    # Automotive
    "car_dealership": {"type": "car_dealer", "keyword": None},
    "garage": {"type": "car_repair", "keyword": None},

    # Sports and retail
    "sports_shop": {"type": "sporting_goods_store", "keyword": None},
    "independent_retailer": {"type": "store", "keyword": "independent"},
}

# Human-readable category names for output
CATEGORY_DISPLAY_NAMES = {
    "pub": "Pub",
    "restaurant": "Restaurant",
    "estate_agent": "Estate Agent",
    "solicitor": "Solicitor",
    "accountant": "Accountancy Firm",
    "insurance_broker": "Insurance Broker",
    "recruitment_agency": "Recruitment Agency",
    "private_healthcare": "Private Healthcare",
    "dental_practice": "Dental Practice",
    "physiotherapy": "Physiotherapy",
    "sports_injury_clinic": "Sports Injury Clinic",
    "gym": "Gym",
    "leisure_centre": "Leisure Centre",
    "construction": "Construction Firm",
    "builder": "Building Firm",
    "supermarket": "Supermarket",
    "tesco": "Tesco",
    "sainsburys": "Sainsbury's",
    "coop": "Co-op",
    "car_dealership": "Car Dealership",
    "garage": "Garage",
    "sports_shop": "Sports Shop",
    "independent_retailer": "Independent Retailer",
}

# Default categories to search (excludes specific supermarket chains by default)
DEFAULT_CATEGORIES = [
    "pub", "restaurant", "estate_agent", "solicitor", "accountant",
    "insurance_broker", "recruitment_agency", "private_healthcare",
    "dental_practice", "physiotherapy", "sports_injury_clinic",
    "gym", "leisure_centre", "construction", "builder", "supermarket",
    "car_dealership", "garage", "sports_shop", "independent_retailer",
]


def validate_uk_postcode(postcode: str) -> bool:
    """
    Validate a UK postcode format.

    Args:
        postcode: The postcode to validate

    Returns:
        True if valid UK postcode format, False otherwise
    """
    # Remove extra spaces and uppercase
    cleaned = postcode.strip().upper()
    return bool(UK_POSTCODE_PATTERN.match(cleaned))


def normalise_postcode(postcode: str) -> str:
    """
    Normalise a UK postcode to standard format.

    Args:
        postcode: The postcode to normalise

    Returns:
        Normalised postcode (uppercase, single space)
    """
    cleaned = postcode.strip().upper()
    # Remove all spaces
    cleaned = cleaned.replace(" ", "")
    # Insert space before last 3 characters
    if len(cleaned) > 3:
        return f"{cleaned[:-3]} {cleaned[-3:]}"
    return cleaned


class BusinessFinder:
    """Find local businesses using Google Maps Places API."""

    def __init__(self, api_key: str):
        """Initialise with Google Maps API key."""
        self.client = googlemaps.Client(key=api_key)

    def geocode_postcode(self, postcode: str) -> Optional[dict]:
        """
        Convert a UK postcode to lat/lng coordinates.

        Args:
            postcode: UK postcode (e.g., "SW1A 1AA" or "M1 1AE")

        Returns:
            Dict with 'lat' and 'lng' keys, or None if not found
        """
        try:
            # Normalise and validate postcode
            normalised = normalise_postcode(postcode)

            if not validate_uk_postcode(normalised):
                print(f"Invalid UK postcode format: {postcode}")
                return None

            # Geocode with UK region bias
            results = self.client.geocode(
                normalised,
                components={"country": "GB"}
            )

            if results:
                geometry = results[0]["geometry"]["location"]
                return {"lat": geometry["lat"], "lng": geometry["lng"]}

        except Exception as e:
            print(f"Error geocoding postcode: {e}")
        return None

    @sleep_and_retry
    @limits(calls=CALLS_PER_SECOND, period=RATE_LIMIT_PERIOD)
    def _rate_limited_places_nearby(self, **kwargs) -> dict:
        """Rate-limited wrapper for places_nearby API call."""
        return self.client.places_nearby(**kwargs)

    @sleep_and_retry
    @limits(calls=CALLS_PER_SECOND, period=RATE_LIMIT_PERIOD)
    def _rate_limited_text_search(self, **kwargs) -> dict:
        """Rate-limited wrapper for text search API call."""
        return self.client.places(**kwargs)

    @sleep_and_retry
    @limits(calls=CALLS_PER_SECOND, period=RATE_LIMIT_PERIOD)
    def _rate_limited_place_details(self, place_id: str) -> dict:
        """Rate-limited wrapper for place details API call."""
        return self.client.place(
            place_id,
            fields=[
                "name", "formatted_address", "formatted_phone_number",
                "website", "place_id", "types", "business_status"
            ]
        )

    def search_businesses(
        self,
        location: dict,
        category_key: str,
        radius: int = 5000
    ) -> list[dict]:
        """
        Search for businesses of a specific category near a location.

        Args:
            location: Dict with 'lat' and 'lng' keys
            category_key: Category key from BUSINESS_CATEGORIES
            radius: Search radius in metres (default 5km)

        Returns:
            List of business dictionaries
        """
        businesses = []
        category = BUSINESS_CATEGORIES.get(category_key, {})
        place_type = category.get("type")
        keyword = category.get("keyword")

        try:
            if place_type:
                # Use nearby search with type
                search_params = {
                    "location": location,
                    "radius": radius,
                    "type": place_type,
                }
                if keyword:
                    search_params["keyword"] = keyword

                response = self._rate_limited_places_nearby(**search_params)
                businesses.extend(response.get("results", []))

                # Handle pagination (up to 60 results total)
                while "next_page_token" in response:
                    time.sleep(2)  # Required delay for pagination
                    response = self._rate_limited_places_nearby(
                        location=location,
                        page_token=response["next_page_token"]
                    )
                    businesses.extend(response.get("results", []))

            elif keyword:
                # Use text search for keyword-only categories
                query = f"{keyword} near {location['lat']},{location['lng']}"
                response = self._rate_limited_text_search(
                    query=keyword,
                    location=location,
                    radius=radius
                )
                businesses.extend(response.get("results", []))

        except Exception as e:
            print(f"Error searching for {category_key}: {e}")

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
        postcode: str,
        radius: int = 5000,
        categories: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Find potential sponsor businesses near a UK postcode.

        Args:
            postcode: UK postcode
            radius: Search radius in metres (default 5km)
            categories: List of category keys to search (default: all)

        Returns:
            List of business dictionaries with details
        """
        # Validate and geocode the postcode
        normalised = normalise_postcode(postcode)
        print(f"Searching near postcode: {normalised}")

        coords = self.geocode_postcode(postcode)
        if not coords:
            print(f"Could not geocode postcode: {postcode}")
            return []

        print(f"Coordinates: {coords['lat']:.6f}, {coords['lng']:.6f}")
        print(f"Search radius: {radius / 1000:.1f} km")

        # Use specified categories or defaults
        search_categories = categories or DEFAULT_CATEGORIES

        # Collect all unique place_ids across categories
        all_place_ids = {}  # place_id -> category_key

        for category_key in search_categories:
            display_name = CATEGORY_DISPLAY_NAMES.get(category_key, category_key)
            print(f"Searching for: {display_name}...")

            results = self.search_businesses(coords, category_key, radius)
            print(f"  Found {len(results)} results")

            for result in results:
                place_id = result.get("place_id")
                if place_id and place_id not in all_place_ids:
                    all_place_ids[place_id] = category_key

        print(f"\nTotal unique businesses found: {len(all_place_ids)}")
        print("Fetching detailed information...")

        # Fetch details for each unique business
        businesses = []
        for i, (place_id, category_key) in enumerate(all_place_ids.items(), 1):
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(all_place_ids)}")

            details = self.get_business_details(place_id)
            if details:
                details["category"] = CATEGORY_DISPLAY_NAMES.get(
                    category_key, category_key
                )
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
        description="Find potential sponsor businesses near a UK postcode"
    )
    parser.add_argument(
        "postcode",
        help="UK postcode (e.g., 'SW1A 1AA' or 'M1 1AE')"
    )
    parser.add_argument(
        "-r", "--radius",
        type=int,
        default=5000,
        help="Search radius in metres (default: 5000)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output CSV filename (default: sponsors_<postcode>_<date>.csv)"
    )
    parser.add_argument(
        "-c", "--categories",
        nargs="+",
        choices=list(BUSINESS_CATEGORIES.keys()),
        help="Specific categories to search (default: all standard categories)"
    )
    parser.add_argument(
        "--include-chains",
        action="store_true",
        help="Include specific supermarket chains (Tesco, Sainsbury's, Co-op)"
    )

    args = parser.parse_args()

    # Validate postcode
    if not validate_uk_postcode(args.postcode):
        print(f"Error: Invalid UK postcode format: {args.postcode}")
        print("Examples of valid formats: SW1A 1AA, M1 1AE, B33 8TH")
        sys.exit(1)

    # Get API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set")
        print("Create a .env file with your API key or set the environment variable")
        sys.exit(1)

    # Determine categories to search
    if args.categories:
        categories = args.categories
    else:
        categories = DEFAULT_CATEGORIES.copy()
        if args.include_chains:
            categories.extend(["tesco", "sainsburys", "coop"])

    # Create finder and search
    finder = BusinessFinder(api_key)
    businesses = finder.find_sponsors(
        args.postcode,
        radius=args.radius,
        categories=categories
    )

    # Generate output filename if not specified
    if args.output:
        output_file = args.output
    else:
        safe_postcode = normalise_postcode(args.postcode).replace(" ", "")
        date_str = datetime.now().strftime("%Y%m%d")
        output_file = f"sponsors_{safe_postcode}_{date_str}.csv"

    # Save results
    save_to_csv(businesses, output_file)


if __name__ == "__main__":
    main()
