#!/usr/bin/env python3
"""
Companies House API Integration

Verifies business legitimacy by checking against the UK Companies House
register. This adds credibility to sponsor prospects by confirming they
are registered, active companies.

API Documentation: https://developer.company-information.service.gov.uk/
"""

import os
import re
import time
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry

load_dotenv()

# Companies House API rate limit: 600 requests per 5 minutes
# We'll use a conservative 2 requests per second
CALLS_PER_SECOND = 2
RATE_LIMIT_PERIOD = 1

# Base URL for Companies House API
COMPANIES_HOUSE_API_BASE = "https://api.company-information.service.gov.uk"


@dataclass
class CompanyInfo:
    """Information about a registered company."""

    company_number: str
    company_name: str
    company_status: str
    company_type: str
    registered_address: str
    date_of_creation: Optional[str] = None
    sic_codes: Optional[list[str]] = None
    is_active: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV export."""
        return {
            "company_number": self.company_number,
            "company_name": self.company_name,
            "company_status": self.company_status,
            "company_type": self.company_type,
            "registered_address": self.registered_address,
            "date_of_creation": self.date_of_creation or "",
            "sic_codes": ",".join(self.sic_codes) if self.sic_codes else "",
            "is_active": self.is_active,
        }


class CompaniesHouseClient:
    """Client for the Companies House API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise the Companies House client.

        Args:
            api_key: Companies House API key. If not provided, will look for
                     COMPANIES_HOUSE_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("COMPANIES_HOUSE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Companies House API key required. Set COMPANIES_HOUSE_API_KEY "
                "environment variable or pass api_key parameter."
            )
        self.session = requests.Session()
        # Companies House uses HTTP Basic Auth with API key as username
        self.session.auth = (self.api_key, "")

    @sleep_and_retry
    @limits(calls=CALLS_PER_SECOND, period=RATE_LIMIT_PERIOD)
    def _rate_limited_get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Make a rate-limited GET request to the API.

        Args:
            endpoint: API endpoint path
            params: Optional query parameters

        Returns:
            JSON response as dictionary
        """
        url = f"{COMPANIES_HOUSE_API_BASE}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def search_companies(
        self,
        query: str,
        items_per_page: int = 10
    ) -> list[dict]:
        """
        Search for companies by name.

        Args:
            query: Company name to search for
            items_per_page: Number of results to return (max 100)

        Returns:
            List of company search results
        """
        try:
            response = self._rate_limited_get(
                "/search/companies",
                params={"q": query, "items_per_page": items_per_page}
            )
            return response.get("items", [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise

    def get_company(self, company_number: str) -> Optional[CompanyInfo]:
        """
        Get detailed information about a specific company.

        Args:
            company_number: Companies House company number

        Returns:
            CompanyInfo object or None if not found
        """
        try:
            # Pad company number to 8 digits if needed
            padded_number = company_number.zfill(8)
            response = self._rate_limited_get(f"/company/{padded_number}")

            # Build registered address string
            address_parts = []
            reg_address = response.get("registered_office_address", {})
            for field in ["address_line_1", "address_line_2", "locality",
                          "region", "postal_code", "country"]:
                if reg_address.get(field):
                    address_parts.append(reg_address[field])
            registered_address = ", ".join(address_parts)

            company_status = response.get("company_status", "")
            is_active = company_status.lower() == "active"

            return CompanyInfo(
                company_number=response.get("company_number", ""),
                company_name=response.get("company_name", ""),
                company_status=company_status,
                company_type=response.get("type", ""),
                registered_address=registered_address,
                date_of_creation=response.get("date_of_creation"),
                sic_codes=response.get("sic_codes"),
                is_active=is_active,
            )

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def verify_business(self, business_name: str) -> Optional[CompanyInfo]:
        """
        Attempt to verify a business by searching Companies House.

        This performs a fuzzy search and returns the best match if found.
        Note: Not all businesses are registered at Companies House (e.g.,
        sole traders, partnerships without limited liability).

        Args:
            business_name: Name of the business to verify

        Returns:
            CompanyInfo for the best match, or None if no match found
        """
        # Clean up the business name for searching
        clean_name = self._clean_business_name(business_name)

        if not clean_name:
            return None

        # Search for companies
        results = self.search_companies(clean_name, items_per_page=5)

        if not results:
            return None

        # Find best match - prioritise active companies
        best_match = None
        for result in results:
            company_number = result.get("company_number")
            if company_number:
                company_info = self.get_company(company_number)
                if company_info:
                    # Prefer active companies
                    if company_info.is_active:
                        return company_info
                    elif not best_match:
                        best_match = company_info

        return best_match

    def _clean_business_name(self, name: str) -> str:
        """
        Clean a business name for Companies House search.

        Removes common suffixes and noise that might interfere with matching.

        Args:
            name: Raw business name

        Returns:
            Cleaned business name
        """
        if not name:
            return ""

        # Remove common location suffixes often added by Google
        cleaned = re.sub(
            r"\s*[-,]\s*(London|Manchester|Birmingham|Leeds|Liverpool|"
            r"Glasgow|Edinburgh|Bristol|Sheffield|Newcastle).*$",
            "",
            name,
            flags=re.IGNORECASE
        )

        # Remove Ltd/Limited if at end (we'll match both forms)
        cleaned = re.sub(
            r"\s+(Ltd\.?|Limited|LLP|PLC|Plc)\.?$",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # Remove possessive forms
        cleaned = re.sub(r"'s\b", "", cleaned)

        # Remove "The" from start
        cleaned = re.sub(r"^The\s+", "", cleaned, flags=re.IGNORECASE)

        return cleaned.strip()


def enrich_businesses_with_ch(
    businesses: list[dict],
    ch_client: CompaniesHouseClient,
    verbose: bool = True
) -> list[dict]:
    """
    Enrich a list of businesses with Companies House data.

    Args:
        businesses: List of business dictionaries (from BusinessFinder)
        ch_client: CompaniesHouseClient instance
        verbose: Whether to print progress

    Returns:
        Enriched list of businesses with Companies House fields added
    """
    enriched = []

    for i, business in enumerate(businesses, 1):
        if verbose and i % 10 == 0:
            print(f"  Companies House lookup: {i}/{len(businesses)}")

        enriched_business = business.copy()

        # Default values for CH fields
        enriched_business["ch_company_number"] = ""
        enriched_business["ch_company_status"] = ""
        enriched_business["ch_verified"] = False

        try:
            company_info = ch_client.verify_business(business.get("name", ""))
            if company_info:
                enriched_business["ch_company_number"] = company_info.company_number
                enriched_business["ch_company_status"] = company_info.company_status
                enriched_business["ch_verified"] = company_info.is_active

                if verbose:
                    status = "✓" if company_info.is_active else "○"
                    print(f"    {status} {business['name']} -> {company_info.company_name}")

        except Exception as e:
            if verbose:
                print(f"    ✗ Error verifying {business.get('name', 'Unknown')}: {e}")

        enriched.append(enriched_business)

        # Small delay between lookups to be kind to the API
        time.sleep(0.1)

    return enriched


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(
        description="Look up a company on Companies House"
    )
    parser.add_argument("company_name", help="Company name to search for")
    args = parser.parse_args()

    try:
        client = CompaniesHouseClient()
        company = client.verify_business(args.company_name)

        if company:
            print(f"\nCompany found:")
            print(f"  Name: {company.company_name}")
            print(f"  Number: {company.company_number}")
            print(f"  Status: {company.company_status}")
            print(f"  Type: {company.company_type}")
            print(f"  Address: {company.registered_address}")
            print(f"  Created: {company.date_of_creation or 'N/A'}")
            print(f"  Active: {'Yes' if company.is_active else 'No'}")
        else:
            print(f"\nNo matching company found for: {args.company_name}")

    except ValueError as e:
        print(f"Error: {e}")
