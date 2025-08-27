#!/usr/bin/env python3
"""
Test Script for Sam's Club Links and Addresses
==============================================

This script validates all Sam's Club URLs and addresses to ensure they are correct
and accessible. It will:

1. Test if each URL is accessible
2. Extract real addresses from club pages
3. Compare with known addresses
4. Generate a validation report

Usage:
    python test_sams_links.py

Author: Vishnu K
Date: 2025-08-26
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import Dict, List, Tuple, Optional
import re

# Import the locations and addresses from the main script
from sams_gas_prices import locations, KNOWN_ADDRESSES

def get_headers() -> Dict[str, str]:
    """Get minimal headers for requests"""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

def test_url_accessibility(url: str, timeout: int = 15) -> Tuple[bool, str, int]:
    """
    Test if a URL is accessible
    
    Returns:
        Tuple of (is_accessible, status_message, status_code)
    """
    try:
        headers = get_headers()
        response = requests.get(url, timeout=timeout, headers=headers)
        
        if response.status_code == 200:
            return True, "OK", response.status_code
        else:
            return False, f"HTTP {response.status_code}", response.status_code
            
    except requests.exceptions.Timeout:
        return False, "Timeout", 0
    except requests.exceptions.ConnectionError:
        return False, "Connection Error", 0
    except requests.exceptions.RequestException as e:
        return False, f"Request Error: {str(e)}", 0
    except Exception as e:
        return False, f"Unexpected Error: {str(e)}", 0

def extract_address_from_page(html_content: str) -> Optional[str]:
    """
    Extract address from HTML content using multiple strategies
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Strategy 1: Look for address tags
    address_elem = soup.find('address')
    if address_elem:
        address_text = address_elem.get_text(strip=True)
        if address_text and len(address_text) > 10:
            return address_text
    
    # Strategy 2: Look for address-like patterns in the entire page
    text = soup.get_text()
    
    # Pattern for US addresses: "Street, City, State ZIP"
    address_patterns = [
        r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl|Circle|Cir|Trail|Trl)[,\s]+[A-Za-z\s]+(?:Arizona|AZ)[,\s]+\d{5}(?:-\d{4})?)',
        r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl|Circle|Cir|Trail|Trl)[,\s]+[A-Za-z\s]+(?:Arizona|AZ)[,\s]+\d{5})',
        r'([A-Za-z\s]+(?:Arizona|AZ)[,\s]+\d{5}(?:-\d{4})?)',
        r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl|Circle|Cir|Trail|Trl)[,\s]+[A-Za-z\s]+(?:Arizona|AZ))'
    ]
    
    for pattern in address_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Return the first match that looks like a real address
            for match in matches:
                if len(match) > 15 and ('AZ' in match or 'Arizona' in match):
                    return match.strip()
    
    # Strategy 3: Look for specific address selectors
    address_selectors = [
        "[data-testid*='address']",
        ".club-address",
        ".address",
        "[class*='address']",
        "[class*='location']",
        "[class*='club-info']"
    ]
    
    for selector in address_selectors:
        try:
            elem = soup.select_one(selector)
            if elem:
                address_text = elem.get_text(strip=True)
                if address_text and len(address_text) > 10:
                    return address_text
        except:
            continue
    
    return None

def validate_club_data() -> Dict:
    """
    Validate all club URLs and addresses
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'total_clubs': len(locations),
        'accessible_urls': 0,
        'inaccessible_urls': 0,
        'addresses_found': 0,
        'addresses_not_found': 0,
        'address_matches': 0,
        'address_mismatches': 0,
        'city_name_validation': 0,
        'city_name_mismatches': 0,
        'detailed_results': []
    }
    
    print("Testing Sam's Club URLs and addresses...")
    print("=" * 60)
    
    for club_name, url in locations.items():
        print(f"\nTesting: {club_name}")
        print(f"URL: {url}")
        
        # Test URL accessibility
        is_accessible, status_msg, status_code = test_url_accessibility(url)
        
        if is_accessible:
            results['accessible_urls'] += 1
            print(f"✓ URL Status: {status_msg}")
            
            # Try to extract address
            try:
                headers = get_headers()
                response = requests.get(url, timeout=15, headers=headers)
                extracted_address = extract_address_from_page(response.text)
                
                if extracted_address:
                    results['addresses_found'] += 1
                    print(f"✓ Extracted Address: {extracted_address}")
                    
                    # Compare with known address
                    known_address = KNOWN_ADDRESSES.get(club_name, "Not found")
                    print(f"  Known Address: {known_address}")
                    
                    # Simple similarity check
                    if known_address != "Not found":
                        if (known_address.lower() in extracted_address.lower() or 
                            extracted_address.lower() in known_address.lower()):
                            results['address_matches'] += 1
                            print("✓ Address Match: Good")
                        else:
                            results['address_mismatches'] += 1
                            print("⚠ Address Mismatch: Check needed")
                    else:
                        print("ℹ No known address to compare")
                    
                    # Validate that city name is in the address
                    city_name = club_name.split(' (')[0] if ' (' in club_name else club_name  # Remove numbering like "(1)" or "(2)"
                    if city_name.lower() in extracted_address.lower():
                        results['city_name_validation'] += 1
                        print(f"✓ City Name Validation: '{city_name}' found in address")
                    else:
                        results['city_name_mismatches'] += 1
                        print(f"⚠ City Name Validation: '{city_name}' NOT found in address")
                        print(f"  Address: {extracted_address}")
                        print(f"  Expected city: {city_name}")
                        
                else:
                    results['addresses_not_found'] += 1
                    print("✗ No address extracted")
                    
            except Exception as e:
                print(f"✗ Error extracting address: {e}")
                results['addresses_not_found'] += 1
                
        else:
            results['inaccessible_urls'] += 1
            print(f"✗ URL Status: {status_msg}")
        
        # Store detailed results
        # Store detailed results
        city_name = club_name.split(' (')[0] if ' (' in club_name else club_name
        city_in_address = city_name.lower() in extracted_address.lower() if extracted_address else False
        
        results['detailed_results'].append({
            'club_name': club_name,
            'url': url,
            'is_accessible': is_accessible,
            'status_message': status_msg,
            'status_code': status_code,
            'extracted_address': extracted_address if is_accessible else None,
            'known_address': KNOWN_ADDRESSES.get(club_name, "Not found"),
            'city_name': city_name,
            'city_in_address': city_in_address
        })
        
        # Add delay to be respectful
        time.sleep(random.uniform(1, 2))
    
    return results

def generate_report(results: Dict) -> None:
    """Generate and display a comprehensive validation report"""
    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)
    
    print(f"Total Clubs Tested: {results['total_clubs']}")
    print(f"Accessible URLs: {results['accessible_urls']}")
    print(f"Inaccessible URLs: {results['inaccessible_urls']}")
    print(f"Addresses Found: {results['addresses_found']}")
    print(f"Addresses Not Found: {results['addresses_not_found']}")
    print(f"Address Matches: {results['address_matches']}")
    print(f"Address Mismatches: {results['address_mismatches']}")
    print(f"City Name Validation: {results['city_name_validation']}")
    print(f"City Name Mismatches: {results['city_name_mismatches']}")
    
    # Calculate success rates
    url_success_rate = (results['accessible_urls'] / results['total_clubs']) * 100
    address_success_rate = (results['addresses_found'] / results['total_clubs']) * 100
    city_validation_rate = (results['city_name_validation'] / results['total_clubs']) * 100
    
    print(f"\nURL Success Rate: {url_success_rate:.1f}%")
    print(f"Address Success Rate: {address_success_rate:.1f}%")
    print(f"City Validation Rate: {city_validation_rate:.1f}%")
    
    # Show detailed results
    print("\n" + "=" * 60)
    print("DETAILED RESULTS")
    print("=" * 60)
    
    for result in results['detailed_results']:
        status_icon = "✓" if result['is_accessible'] else "✗"
        print(f"\n{status_icon} {result['club_name']}")
        print(f"  URL: {result['url']}")
        print(f"  Status: {result['status_message']}")
        
        if result['is_accessible']:
            if result['extracted_address']:
                print(f"  Extracted: {result['extracted_address']}")
                print(f"  Known: {result['known_address']}")
                
                # Show city validation status
                city_icon = "✓" if result['city_in_address'] else "⚠"
                print(f"  City Validation: {city_icon} {result['city_name']}")
            else:
                print(f"  Address: Not extracted")
        else:
            print(f"  Address: Cannot check (URL inaccessible)")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if results['inaccessible_urls'] > 0:
        print(f"⚠ {results['inaccessible_urls']} URLs are not accessible. Check these:")
        for result in results['detailed_results']:
            if not result['is_accessible']:
                print(f"  - {result['club_name']}: {result['status_message']}")
    
    if results['address_mismatches'] > 0:
        print(f"⚠ {results['address_mismatches']} addresses don't match. Verify these:")
        for result in results['detailed_results']:
            if result['extracted_address'] and result['known_address'] != "Not found":
                if not (result['known_address'].lower() in result['extracted_address'].lower() or 
                       result['extracted_address'].lower() in result['known_address'].lower()):
                    print(f"  - {result['club_name']}")
                    print(f"    Known: {result['known_address']}")
                    print(f"    Extracted: {result['extracted_address']}")
    
    if results['addresses_not_found'] > 0:
        print(f"ℹ {results['addresses_not_found']} addresses couldn't be extracted. Consider manual verification.")
    
    if results['city_name_mismatches'] > 0:
        print(f"⚠ {results['city_name_mismatches']} addresses don't contain the expected city name. Check these:")
        for result in results['detailed_results']:
            if result['extracted_address'] and not result['city_in_address']:
                print(f"  - {result['club_name']}: Expected '{result['city_name']}' in address")
                print(f"    Address: {result['extracted_address']}")
    
    if results['accessible_urls'] == results['total_clubs'] and results['addresses_found'] == results['total_clubs'] and results['city_name_validation'] == results['total_clubs']:
        print("🎉 All URLs are accessible, addresses were found, and city names are validated!")
    elif results['accessible_urls'] == results['total_clubs'] and results['addresses_found'] == results['total_clubs']:
        print("🎉 All URLs are accessible and addresses were found!")

def main():
    """Main execution function"""
    print("Sam's Club Link and Address Validator")
    print("=" * 60)
    
    try:
        # Run validation
        results = validate_club_data()
        
        # Generate report
        generate_report(results)
        
        # Save results to file
        with open('validation_report.txt', 'w') as f:
            f.write("Sam's Club Validation Report\n")
            f.write("=" * 30 + "\n\n")
            f.write(f"Total Clubs: {results['total_clubs']}\n")
            f.write(f"Accessible URLs: {results['accessible_urls']}\n")
            f.write(f"Addresses Found: {results['addresses_found']}\n")
            f.write(f"Address Matches: {results['address_matches']}\n")
            f.write(f"City Name Validation: {results['city_name_validation']}\n")
            f.write(f"City Name Mismatches: {results['city_name_mismatches']}\n\n")
            
            for result in results['detailed_results']:
                f.write(f"{result['club_name']}:\n")
                f.write(f"  URL: {result['url']}\n")
                f.write(f"  Accessible: {result['is_accessible']}\n")
                f.write(f"  Status: {result['status_message']}\n")
                if result['extracted_address']:
                    f.write(f"  Address: {result['extracted_address']}\n")
                    f.write(f"  City Validation: {result['city_name']} - {'✓' if result['city_in_address'] else '⚠'}\n")
                f.write("\n")
        
        print(f"\nDetailed report saved to: validation_report.txt")
        
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
    except Exception as e:
        print(f"\nError during validation: {e}")

if __name__ == "__main__":
    main()
