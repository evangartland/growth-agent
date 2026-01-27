#!/usr/bin/env python3
"""
SponsorScout UK - Main Entry Point

Combines Google Maps business discovery with Companies House verification
to find and validate potential sponsors for UK sports clubs.
"""

import argparse
import csv
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from business_finder import (
    BUSINESS_CATEGORIES,
    DEFAULT_CATEGORIES,
    BusinessFinder,
    normalise_postcode,
    validate_uk_postcode,
)
from companies_house import CompaniesHouseClient, enrich_businesses_with_ch

load_dotenv()


def save_results(
    businesses: list[dict],
    filename: str,
    include_ch: bool = False
) -> None:
    """
    Save results to CSV file.

    Args:
        businesses: List of business dictionaries
        filename: Output filename
        include_ch: Whether Companies House fields are included
    """
    if not businesses:
        print("No businesses to save")
        return

    # Define fields based on whether CH data is included
    fieldnames = ["name", "category", "address", "phone", "website", "place_id"]

    if include_ch:
        fieldnames.extend(["ch_company_number", "ch_company_status", "ch_verified"])

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(businesses)

    print(f"\nSaved {len(businesses)} businesses to {filename}")


def main():
    """Main entry point for SponsorScout UK."""
    parser = argparse.ArgumentParser(
        description="Find and verify potential sponsor businesses near a UK postcode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s SW1A1AA                     Search near Westminster (5km radius)
  %(prog)s "M1 1AE" -r 10000           Search Manchester, 10km radius
  %(prog)s E14 5AB --verify            Include Companies House verification
  %(prog)s N1 9GU -c pub restaurant    Search only pubs and restaurants
  %(prog)s SE1 7PB --include-chains    Include Tesco, Sainsbury's, Co-op
        """
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
        metavar="CATEGORY",
        help="Specific categories to search (default: all standard categories)"
    )
    parser.add_argument(
        "--include-chains",
        action="store_true",
        help="Include specific supermarket chains (Tesco, Sainsbury's, Co-op)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify businesses against Companies House (requires API key)"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available business categories and exit"
    )

    args = parser.parse_args()

    # Handle --list-categories
    if args.list_categories:
        print("Available business categories:")
        for key in sorted(BUSINESS_CATEGORIES.keys()):
            print(f"  {key}")
        sys.exit(0)

    # Validate postcode
    if not validate_uk_postcode(args.postcode):
        print(f"Error: Invalid UK postcode format: {args.postcode}")
        print("Examples of valid formats: SW1A 1AA, M1 1AE, B33 8TH, CR2 6XH")
        sys.exit(1)

    # Check for Google Maps API key
    google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not google_api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set")
        print("Create a .env file with your API key or set the environment variable")
        sys.exit(1)

    # Check for Companies House API key if verification requested
    ch_client = None
    if args.verify:
        ch_api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
        if not ch_api_key:
            print("Warning: COMPANIES_HOUSE_API_KEY not set, skipping verification")
            args.verify = False
        else:
            ch_client = CompaniesHouseClient(ch_api_key)

    # Determine categories to search
    if args.categories:
        categories = args.categories
    else:
        categories = DEFAULT_CATEGORIES.copy()
        if args.include_chains:
            categories.extend(["tesco", "sainsburys", "coop"])

    # Print banner
    print("=" * 60)
    print("SponsorScout UK - Local Business Finder")
    print("=" * 60)

    # Find businesses
    finder = BusinessFinder(google_api_key)
    businesses = finder.find_sponsors(
        args.postcode,
        radius=args.radius,
        categories=categories
    )

    if not businesses:
        print("No businesses found")
        sys.exit(0)

    # Optionally verify with Companies House
    if args.verify and ch_client:
        print("\nVerifying businesses with Companies House...")
        businesses = enrich_businesses_with_ch(businesses, ch_client, verbose=True)

        # Print summary
        verified_count = sum(1 for b in businesses if b.get("ch_verified"))
        print(f"\nVerification complete: {verified_count}/{len(businesses)} "
              f"businesses verified as active companies")

    # Generate output filename
    if args.output:
        output_file = args.output
    else:
        safe_postcode = normalise_postcode(args.postcode).replace(" ", "")
        date_str = datetime.now().strftime("%Y%m%d")
        output_file = f"sponsors_{safe_postcode}_{date_str}.csv"

    # Save results
    save_results(businesses, output_file, include_ch=args.verify)

    print("\nDone!")


if __name__ == "__main__":
    main()
