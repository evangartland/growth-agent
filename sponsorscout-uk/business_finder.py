#!/usr/bin/env python3
"""
SponsorScout UK - Local Business Finder

Finds potential sponsor businesses near a given UK postcode using
Google Maps Places API. Optimised for UK sports clubs seeking
local sponsorship opportunities.

Features:
- UK postcode validation and geocoding
- Tier-based categorisation (Priority/Strong/Potential)
- Sponsorship scoring (1-10)
- Chain vs independent detection
- Business enrichment (emails, social media)
- Companies House verification integration
"""

import argparse
import csv
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import googlemaps
import requests
from bs4 import BeautifulSoup
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

# =============================================================================
# TIER CLASSIFICATION
# =============================================================================

# Tier 1 - Priority: High-fit sponsors (sports-related, health & fitness)
TIER_1_PRIORITY = [
    "gym", "leisure_centre", "sports_shop", "physiotherapy",
    "sports_injury_clinic", "sports_brand"
]

# Tier 2 - Strong: Medium-fit sponsors (local community businesses)
TIER_2_STRONG = [
    "pub", "restaurant", "estate_agent", "construction", "builder",
    "car_dealership", "garage", "dental_practice", "private_healthcare"
]

# Tier 3 - Potential: Lower-fit but still viable sponsors
TIER_3_POTENTIAL = [
    "solicitor", "accountant", "insurance_broker", "recruitment_agency",
    "supermarket", "independent_retailer", "tesco", "sainsburys", "coop"
]

# =============================================================================
# KNOWN UK CHAINS (for independent vs chain detection)
# =============================================================================

UK_CHAIN_PATTERNS = [
    # Supermarkets
    r"\btesco\b", r"\bsainsbury'?s?\b", r"\basda\b", r"\bmorrisons\b",
    r"\bwaitrose\b", r"\blidl\b", r"\baldi\b", r"\bco-?op\b", r"\bm&s\b",
    r"\bmarks\s*(&|and)\s*spencer\b",

    # Pubs/Restaurants
    r"\bwetherspoon\b", r"\bgreene\s*king\b", r"\bmarstons\b",
    r"\bmitchells\s*(&|and)\s*butlers\b", r"\bnandos?\b", r"\bfrankie\s*(&|and)\s*benny'?s?\b",
    r"\bpizza\s*(express|hut)\b", r"\bdominos?\b", r"\bkfc\b",
    r"\bmcdonalds?\b", r"\bburger\s*king\b", r"\bsubway\b", r"\bcosta\b",
    r"\bstarbucks\b", r"\bpret\s*a\s*manger\b", r"\bcaffe\s*nero\b",

    # Gyms
    r"\bpuregym\b", r"\bthe\s*gym\s*group\b", r"\bvirgin\s*active\b",
    r"\bdavid\s*lloyd\b", r"\bnuffield\b", r"\bbannatyne\b",
    r"\beveryone\s*active\b", r"\bbetter\s*leisure\b", r"\bfitness\s*first\b",
    r"\banytime\s*fitness\b",

    # Estate Agents
    r"\bfoxtons\b", r"\bknight\s*frank\b", r"\bsavills\b",
    r"\bcountrywide\b", r"\bpurplebricks?\b", r"\byopa\b",
    r"\bconnells\b", r"\bbairstow\s*eves\b", r"\bsequence\b",

    # Healthcare
    r"\bbupa\b", r"\bnuffield\s*health\b", r"\bspire\b", r"\bbmi\s*healthcare\b",
    r"\bmydentist\b", r"\bportman\s*dental\b",

    # Automotive
    r"\bkwik\s*fit\b", r"\bhalfords\b", r"\bnational\s*tyres\b",
    r"\barnold\s*clark\b", r"\bevans\s*halshaw\b", r"\bsytner\b",
    r"\bpendragon\b", r"\blooki?ng?\s*local\b",

    # General retail
    r"\bboots\b", r"\bsuperdrug\b", r"\bwh\s*smith\b", r"\bcurrys\b",
    r"\bargos\b", r"\bb&q\b", r"\bhomebase\b", r"\bscrewfix\b",
    r"\btoolstation\b", r"\bsports\s*direct\b", r"\bjd\s*sports\b",
    r"\bjjb\b", r"\bdecathlon\b",

    # Professional services chains
    r"\bh&r\s*block\b", r"\btaxassist\b", r"\bspecsavers\b",
]

# Compile chain patterns for efficiency
CHAIN_REGEX = re.compile("|".join(UK_CHAIN_PATTERNS), re.IGNORECASE)

# =============================================================================
# BUSINESS CATEGORIES
# =============================================================================

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

DEFAULT_CATEGORIES = [
    "pub", "restaurant", "estate_agent", "solicitor", "accountant",
    "insurance_broker", "recruitment_agency", "private_healthcare",
    "dental_practice", "physiotherapy", "sports_injury_clinic",
    "gym", "leisure_centre", "construction", "builder", "supermarket",
    "car_dealership", "garage", "sports_shop", "independent_retailer",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_uk_postcode(postcode: str) -> bool:
    """Validate a UK postcode format."""
    cleaned = postcode.strip().upper()
    return bool(UK_POSTCODE_PATTERN.match(cleaned))


def normalise_postcode(postcode: str) -> str:
    """Normalise a UK postcode to standard format (uppercase, single space)."""
    cleaned = postcode.strip().upper().replace(" ", "")
    if len(cleaned) > 3:
        return f"{cleaned[:-3]} {cleaned[-3:]}"
    return cleaned


def clean_business_name(name: str) -> str:
    """
    Clean UK business name for display.

    Removes common suffixes like Ltd, Limited, LLP, PLC and standardises formatting.
    """
    if not name:
        return ""

    cleaned = name.strip()

    # Remove common UK business suffixes
    suffixes_pattern = r"\s*[\(\[]?(Ltd\.?|Limited|LLP|PLC|Plc|Inc\.?|UK|GB)[\)\]]?\.?\s*$"
    cleaned = re.sub(suffixes_pattern, "", cleaned, flags=re.IGNORECASE)

    # Remove trailing punctuation
    cleaned = re.sub(r"[,\.\-]+$", "", cleaned).strip()

    # Standardise common abbreviations
    cleaned = re.sub(r"\bSt\b", "Street", cleaned)
    cleaned = re.sub(r"\bRd\b", "Road", cleaned)

    return cleaned


def is_chain_business(name: str, website: str = "") -> bool:
    """
    Detect if a business is a chain/franchise rather than independent.

    Args:
        name: Business name
        website: Business website URL

    Returns:
        True if likely a chain, False if likely independent
    """
    # Check name against known chains
    if CHAIN_REGEX.search(name):
        return True

    # Check website domain for chain indicators
    if website:
        try:
            domain = urlparse(website).netloc.lower()
            if CHAIN_REGEX.search(domain):
                return True
        except Exception:
            pass

    return False


def get_tier(category_key: str) -> tuple[int, str]:
    """
    Get sponsorship tier for a business category.

    Returns:
        Tuple of (tier_number, tier_name)
    """
    if category_key in TIER_1_PRIORITY:
        return (1, "Priority")
    elif category_key in TIER_2_STRONG:
        return (2, "Strong")
    else:
        return (3, "Potential")


def calculate_score(
    category_key: str,
    is_independent: bool,
    has_website: bool,
    has_phone: bool,
    distance_metres: Optional[float] = None,
    ch_verified: bool = False,
    has_email: bool = False,
    has_social: bool = False
) -> int:
    """
    Calculate sponsorship potential score (1-10) for a business.

    Scoring factors:
    - Category relevance to community sport (base score from tier)
    - Independent vs chain (+2 for independent)
    - Website presence (+1)
    - Phone number (+0.5)
    - Distance from postcode (closer = higher)
    - Companies House verified (+1)
    - Contact email found (+0.5)
    - Social media presence (+0.5)
    """
    # Base score from tier (Tier 1: 7, Tier 2: 5, Tier 3: 3)
    tier_num, _ = get_tier(category_key)
    if tier_num == 1:
        score = 7.0
    elif tier_num == 2:
        score = 5.0
    else:
        score = 3.0

    # Independent businesses score higher (+2)
    if is_independent:
        score += 2.0

    # Web presence
    if has_website:
        score += 1.0

    # Phone availability
    if has_phone:
        score += 0.5

    # Distance bonus (closer is better)
    if distance_metres is not None:
        if distance_metres < 1000:
            score += 1.0
        elif distance_metres < 2000:
            score += 0.5

    # Companies House verified
    if ch_verified:
        score += 1.0

    # Contact availability
    if has_email:
        score += 0.5
    if has_social:
        score += 0.5

    # Cap at 10
    return min(10, max(1, round(score)))


# =============================================================================
# BUSINESS ENRICHMENT
# =============================================================================

class BusinessEnricher:
    """Enrich business data with emails, social media, and other details."""

    # Common UK email patterns
    EMAIL_PATTERNS = [
        r"info@", r"enquiries@", r"enquiry@", r"contact@", r"hello@",
        r"admin@", r"office@", r"reception@", r"bookings@", r"sales@",
        r"team@", r"support@",
    ]

    # Social media URL patterns
    SOCIAL_PATTERNS = {
        "facebook": r"facebook\.com/[\w\.\-]+",
        "twitter": r"(?:twitter|x)\.com/[\w]+",
        "instagram": r"instagram\.com/[\w\.]+",
        "linkedin": r"linkedin\.com/(?:company|in)/[\w\-]+",
    }

    def __init__(self, timeout: int = 5):
        """Initialise enricher with request timeout."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; SponsorScout/1.0)"
        })

    @sleep_and_retry
    @limits(calls=2, period=1)  # Rate limit website scraping
    def _fetch_website(self, url: str) -> Optional[str]:
        """Fetch website content with rate limiting."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception:
            return None

    def find_email(self, website: str) -> Optional[str]:
        """
        Try to find a contact email from a business website.

        Args:
            website: Business website URL

        Returns:
            Email address if found, None otherwise
        """
        if not website:
            return None

        html = self._fetch_website(website)
        if not html:
            return None

        # Look for email addresses in the HTML
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, html)

        if not emails:
            return None

        # Filter out common junk emails
        junk_patterns = [
            r"example\.com", r"domain\.com", r"email\.com",
            r"sentry", r"wixpress", r"schema\.org",
        ]

        for email in emails:
            email_lower = email.lower()
            # Skip junk emails
            if any(re.search(p, email_lower) for p in junk_patterns):
                continue
            # Prefer common contact patterns
            for pattern in self.EMAIL_PATTERNS:
                if re.match(pattern, email_lower):
                    return email
            # Return first valid-looking email
            return email

        return None

    def find_social_media(self, website: str) -> dict[str, str]:
        """
        Find social media links from a business website.

        Args:
            website: Business website URL

        Returns:
            Dict of platform -> URL
        """
        social_links = {}

        if not website:
            return social_links

        html = self._fetch_website(website)
        if not html:
            return social_links

        for platform, pattern in self.SOCIAL_PATTERNS.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                # Take first unique match
                url = matches[0]
                if not url.startswith("http"):
                    url = f"https://{url}"
                social_links[platform] = url

        return social_links

    def enrich_business(self, business: dict, verbose: bool = False) -> dict:
        """
        Enrich a business record with additional contact details.

        Args:
            business: Business dictionary
            verbose: Whether to print progress

        Returns:
            Enriched business dictionary
        """
        enriched = business.copy()

        # Default enrichment fields
        enriched.setdefault("email", "")
        enriched.setdefault("facebook", "")
        enriched.setdefault("twitter", "")
        enriched.setdefault("instagram", "")
        enriched.setdefault("linkedin", "")
        enriched.setdefault("contact_method", "")

        website = business.get("website", "")

        if website:
            try:
                # Find email
                email = self.find_email(website)
                if email:
                    enriched["email"] = email
                    if verbose:
                        print(f"    Found email: {email}")

                # Find social media
                social = self.find_social_media(website)
                for platform, url in social.items():
                    enriched[platform] = url

            except Exception as e:
                if verbose:
                    print(f"    Error enriching: {e}")

        # Set recommended contact method
        if enriched["email"]:
            enriched["contact_method"] = "Email"
        elif enriched["phone"]:
            enriched["contact_method"] = "Phone"
        else:
            enriched["contact_method"] = "Visit website"

        return enriched


# =============================================================================
# MAIN BUSINESS FINDER CLASS
# =============================================================================

@dataclass
class ScoredBusiness:
    """Business record with scoring and enrichment data."""
    name: str
    display_name: str
    category: str
    category_key: str
    address: str
    phone: str
    website: str
    place_id: str
    tier: int
    tier_name: str
    score: int
    is_independent: bool
    email: str = ""
    contact_method: str = ""
    facebook: str = ""
    twitter: str = ""
    instagram: str = ""
    linkedin: str = ""
    ch_verified: bool = False
    ch_company_number: str = ""
    distance_metres: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV export."""
        return {
            "name": self.display_name,
            "original_name": self.name,
            "category": self.category,
            "tier": self.tier_name,
            "score": self.score,
            "is_independent": "Yes" if self.is_independent else "No",
            "address": self.address,
            "phone": self.phone,
            "website": self.website,
            "email": self.email,
            "contact_method": self.contact_method,
            "facebook": self.facebook,
            "twitter": self.twitter,
            "instagram": self.instagram,
            "linkedin": self.linkedin,
            "ch_verified": "Yes" if self.ch_verified else "",
            "ch_company_number": self.ch_company_number,
            "place_id": self.place_id,
        }


class BusinessFinder:
    """Find and score local businesses using Google Maps Places API."""

    def __init__(self, api_key: str):
        """Initialise with Google Maps API key."""
        self.client = googlemaps.Client(key=api_key)
        self.enricher = BusinessEnricher()

    def geocode_postcode(self, postcode: str) -> Optional[dict]:
        """Convert a UK postcode to lat/lng coordinates."""
        try:
            normalised = normalise_postcode(postcode)

            if not validate_uk_postcode(normalised):
                print(f"Invalid UK postcode format: {postcode}")
                return None

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
                "website", "place_id", "types", "business_status", "geometry"
            ]
        )

    def search_businesses(
        self,
        location: dict,
        category_key: str,
        radius: int = 5000
    ) -> list[dict]:
        """Search for businesses of a specific category near a location."""
        businesses = []
        category = BUSINESS_CATEGORIES.get(category_key, {})
        place_type = category.get("type")
        keyword = category.get("keyword")

        try:
            if place_type:
                search_params = {
                    "location": location,
                    "radius": radius,
                    "type": place_type,
                }
                if keyword:
                    search_params["keyword"] = keyword

                response = self._rate_limited_places_nearby(**search_params)
                businesses.extend(response.get("results", []))

                # Handle pagination
                while "next_page_token" in response:
                    time.sleep(2)
                    response = self._rate_limited_places_nearby(
                        location=location,
                        page_token=response["next_page_token"]
                    )
                    businesses.extend(response.get("results", []))

            elif keyword:
                response = self._rate_limited_text_search(
                    query=keyword,
                    location=location,
                    radius=radius
                )
                businesses.extend(response.get("results", []))

        except Exception as e:
            print(f"Error searching for {category_key}: {e}")

        return businesses

    def get_business_details(
        self,
        place_id: str,
        origin_coords: Optional[dict] = None
    ) -> Optional[dict]:
        """Get detailed information for a specific business."""
        try:
            result = self._rate_limited_place_details(place_id)
            if result and "result" in result:
                place = result["result"]
                if place.get("business_status") == "OPERATIONAL":
                    details = {
                        "name": place.get("name", ""),
                        "address": place.get("formatted_address", ""),
                        "phone": place.get("formatted_phone_number", ""),
                        "website": place.get("website", ""),
                        "place_id": place.get("place_id", ""),
                    }

                    # Calculate distance if origin provided
                    if origin_coords and "geometry" in place:
                        loc = place["geometry"]["location"]
                        details["distance_metres"] = self._haversine_distance(
                            origin_coords["lat"], origin_coords["lng"],
                            loc["lat"], loc["lng"]
                        )

                    return details
        except Exception as e:
            print(f"Error getting details for {place_id}: {e}")
        return None

    @staticmethod
    def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two coordinates in metres."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # Earth's radius in metres

        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def find_sponsors(
        self,
        postcode: str,
        radius: int = 5000,
        categories: Optional[list[str]] = None,
        enrich: bool = True,
        ch_client=None,
        verbose: bool = True
    ) -> list[ScoredBusiness]:
        """
        Find and score potential sponsor businesses near a UK postcode.

        Args:
            postcode: UK postcode
            radius: Search radius in metres
            categories: Category keys to search (default: all)
            enrich: Whether to enrich with emails/social media
            ch_client: Optional CompaniesHouseClient for verification
            verbose: Print progress

        Returns:
            List of ScoredBusiness objects, sorted by score (highest first)
        """
        normalised = normalise_postcode(postcode)
        if verbose:
            print(f"Searching near postcode: {normalised}")

        coords = self.geocode_postcode(postcode)
        if not coords:
            print(f"Could not geocode postcode: {postcode}")
            return []

        if verbose:
            print(f"Coordinates: {coords['lat']:.6f}, {coords['lng']:.6f}")
            print(f"Search radius: {radius / 1000:.1f} km")

        search_categories = categories or DEFAULT_CATEGORIES

        # Collect unique place_ids
        all_place_ids = {}

        for category_key in search_categories:
            display_name = CATEGORY_DISPLAY_NAMES.get(category_key, category_key)
            if verbose:
                print(f"Searching for: {display_name}...")

            results = self.search_businesses(coords, category_key, radius)
            if verbose:
                print(f"  Found {len(results)} results")

            for result in results:
                place_id = result.get("place_id")
                if place_id and place_id not in all_place_ids:
                    all_place_ids[place_id] = category_key

        if verbose:
            print(f"\nTotal unique businesses found: {len(all_place_ids)}")
            print("Fetching detailed information...")

        # Fetch details and build scored businesses
        businesses = []
        for i, (place_id, category_key) in enumerate(all_place_ids.items(), 1):
            if verbose and i % 20 == 0:
                print(f"  Progress: {i}/{len(all_place_ids)}")

            details = self.get_business_details(place_id, origin_coords=coords)
            if not details:
                continue

            # Determine if independent
            is_independent = not is_chain_business(
                details["name"],
                details.get("website", "")
            )

            # Get tier
            tier_num, tier_name = get_tier(category_key)

            # Enrich if requested
            enriched = details.copy()
            if enrich:
                if verbose and i == 1:
                    print("  Enriching business data (emails, social media)...")
                enriched = self.enricher.enrich_business(details, verbose=False)

            # Companies House verification if available
            ch_verified = False
            ch_number = ""
            if ch_client:
                try:
                    company = ch_client.verify_business(details["name"])
                    if company and company.is_active:
                        ch_verified = True
                        ch_number = company.company_number
                except Exception:
                    pass

            # Calculate score
            score = calculate_score(
                category_key=category_key,
                is_independent=is_independent,
                has_website=bool(details.get("website")),
                has_phone=bool(details.get("phone")),
                distance_metres=details.get("distance_metres"),
                ch_verified=ch_verified,
                has_email=bool(enriched.get("email")),
                has_social=bool(
                    enriched.get("facebook") or
                    enriched.get("twitter") or
                    enriched.get("instagram")
                )
            )

            business = ScoredBusiness(
                name=details["name"],
                display_name=clean_business_name(details["name"]),
                category=CATEGORY_DISPLAY_NAMES.get(category_key, category_key),
                category_key=category_key,
                address=details["address"],
                phone=details.get("phone", ""),
                website=details.get("website", ""),
                place_id=details["place_id"],
                tier=tier_num,
                tier_name=tier_name,
                score=score,
                is_independent=is_independent,
                email=enriched.get("email", ""),
                contact_method=enriched.get("contact_method", ""),
                facebook=enriched.get("facebook", ""),
                twitter=enriched.get("twitter", ""),
                instagram=enriched.get("instagram", ""),
                linkedin=enriched.get("linkedin", ""),
                ch_verified=ch_verified,
                ch_company_number=ch_number,
                distance_metres=details.get("distance_metres"),
            )

            businesses.append(business)

        # Sort by score (highest first), then by tier
        businesses.sort(key=lambda b: (-b.score, b.tier))

        if verbose:
            print(f"\nSuccessfully processed {len(businesses)} businesses")
            self._print_summary(businesses)

        return businesses

    def _print_summary(self, businesses: list[ScoredBusiness]) -> None:
        """Print summary statistics."""
        if not businesses:
            return

        tier_counts = {1: 0, 2: 0, 3: 0}
        independent_count = 0
        with_email = 0
        with_website = 0

        for b in businesses:
            tier_counts[b.tier] = tier_counts.get(b.tier, 0) + 1
            if b.is_independent:
                independent_count += 1
            if b.email:
                with_email += 1
            if b.website:
                with_website += 1

        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"Total businesses: {len(businesses)}")
        print(f"  Tier 1 (Priority): {tier_counts.get(1, 0)}")
        print(f"  Tier 2 (Strong):   {tier_counts.get(2, 0)}")
        print(f"  Tier 3 (Potential): {tier_counts.get(3, 0)}")
        print(f"\nIndependent: {independent_count} ({100*independent_count//len(businesses)}%)")
        print(f"With website: {with_website}")
        print(f"With email found: {with_email}")
        print(f"\nTop 5 prospects:")
        for b in businesses[:5]:
            ind = "★" if b.is_independent else "○"
            print(f"  {ind} {b.display_name} ({b.category}) - Score: {b.score}/10")


def save_to_csv(businesses: list[ScoredBusiness], filename: str) -> None:
    """Save scored business data to CSV file."""
    if not businesses:
        print("No businesses to save")
        return

    fieldnames = [
        "name", "category", "tier", "score", "is_independent",
        "address", "phone", "website", "email", "contact_method",
        "facebook", "twitter", "instagram", "linkedin",
        "ch_verified", "ch_company_number", "place_id", "original_name"
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for business in businesses:
            writer.writerow(business.to_dict())

    print(f"\nSaved {len(businesses)} businesses to {filename}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Find and score potential sponsor businesses near a UK postcode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "SW1A 1AA"                    Search Westminster (5km)
  %(prog)s --postcode "SW1A 1AA"         Same with flag
  %(prog)s "M1 1AE" --radius 3000        Search Manchester (3km)
  %(prog)s "E14 5AB" --no-enrich         Skip email/social enrichment
  %(prog)s "N1 9GU" -c pub restaurant    Search specific categories
        """
    )

    # Support both positional and flag-based postcode
    parser.add_argument(
        "postcode_positional",
        nargs="?",
        help="UK postcode (e.g., 'SW1A 1AA')"
    )
    parser.add_argument(
        "-p", "--postcode",
        help="UK postcode (alternative to positional argument)"
    )
    parser.add_argument(
        "-r", "--radius",
        type=int,
        default=5000,
        help="Search radius in metres (default: 5000)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output CSV filename"
    )
    parser.add_argument(
        "-c", "--categories",
        nargs="+",
        choices=list(BUSINESS_CATEGORIES.keys()),
        metavar="CATEGORY",
        help="Specific categories to search"
    )
    parser.add_argument(
        "--include-chains",
        action="store_true",
        help="Include supermarket chains (Tesco, Sainsbury's, Co-op)"
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip email and social media enrichment"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify with Companies House (requires API key)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Minimal output"
    )

    args = parser.parse_args()

    # Determine postcode (flag takes precedence)
    postcode = args.postcode or args.postcode_positional
    if not postcode:
        parser.error("Postcode is required (use positional or --postcode)")

    # Validate postcode
    if not validate_uk_postcode(postcode):
        print(f"Error: Invalid UK postcode format: {postcode}")
        print("Examples: SW1A 1AA, M1 1AE, B33 8TH, E14 5AB")
        sys.exit(1)

    # Check API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set")
        sys.exit(1)

    # Companies House client if verification requested
    ch_client = None
    if args.verify:
        ch_api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
        if ch_api_key:
            from companies_house import CompaniesHouseClient
            ch_client = CompaniesHouseClient(ch_api_key)
        else:
            print("Warning: COMPANIES_HOUSE_API_KEY not set, skipping verification")

    # Determine categories
    if args.categories:
        categories = args.categories
    else:
        categories = DEFAULT_CATEGORIES.copy()
        if args.include_chains:
            categories.extend(["tesco", "sainsburys", "coop"])

    # Print banner
    if not args.quiet:
        print("=" * 60)
        print("SponsorScout UK - Local Business Finder")
        print("=" * 60)

    # Find and score businesses
    finder = BusinessFinder(api_key)
    businesses = finder.find_sponsors(
        postcode=postcode,
        radius=args.radius,
        categories=categories,
        enrich=not args.no_enrich,
        ch_client=ch_client,
        verbose=not args.quiet
    )

    if not businesses:
        print("No businesses found")
        sys.exit(0)

    # Generate output filename
    if args.output:
        output_file = args.output
    else:
        safe_postcode = normalise_postcode(postcode).replace(" ", "")
        date_str = datetime.now().strftime("%Y%m%d")
        output_file = f"sponsors_{safe_postcode}_{date_str}.csv"

    # Save results
    save_to_csv(businesses, output_file)


if __name__ == "__main__":
    main()
