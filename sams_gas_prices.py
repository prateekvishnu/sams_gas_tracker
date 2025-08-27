"""
Sam's Club Gas Price Scraper with Smart History Management
==========================================================

This script manages Sam's Club gas price data with enhanced features and smart scraping logic.
Due to bot protection, it works with known data and allows manual updates.

Features:
- Manages gas prices from known Sam's Club locations
- Extracts club names, addresses, and fuel center URLs when possible
- Identifies lowest prices for each fuel category
- Allows adding new club links and manual price updates
- Comprehensive error handling with "couldn't fetch/NAN" messages
- Address extraction from club pages (when accessible)
- CSV export and data management
- SMART SCRAPING: Only scrapes locations not scraped today
- COMPREHENSIVE HISTORY: Stores all price data with timestamps
- EFFICIENCY: Skips scraping if all locations were scraped today

Usage:
    python sams_gas_prices_2.py

Output:
    - Console display of all club information
    - CSV file with club data
    - Lowest price identification for each fuel type
    - Historical data analysis

Author: Vishnu K
Date: 2025-08-26
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from typing import List, Dict, Optional, Tuple
import time
import random
import json
import os
from datetime import datetime, date
import sqlite3

BASE_URL = "https://www.samsclub.com"

# List of Sam's Club Arizona fuel center URLs (proven working)
locations = {
    "Avondale": "https://www.samsclub.com/club/4830-avondale-az",
    "Bullhead City": "https://www.samsclub.com/club/4915-bullhead-city-az",
    "Chandler": "https://www.samsclub.com/club/6213-chandler-az",
    "Flagstaff": "https://www.samsclub.com/club/6604-flagstaff-az",
    "Gilbert (1)": "https://www.samsclub.com/club/6605-gilbert-az",
    "Gilbert (2)": "https://www.samsclub.com/club/4829-gilbert-az",
    "Glendale": "https://www.samsclub.com/club/4732-glendale-az",
    "Phoenix (1)": "https://www.samsclub.com/club/6606-phoenix-az",
    "Phoenix (2)": "https://www.samsclub.com/club/6608-phoenix-az",
    "Surprise": "https://www.samsclub.com/club/4955-surprise-az",
    "Tucson": "https://www.samsclub.com/club/6692-tucson-az",
    "Yuma": "https://www.samsclub.com/club/6205-yuma-az",
}

# Additional club links that can be manually added
ADDITIONAL_CLUBS = {
    # Add new clubs here in format: "Club Name": "Club URL"
    # Example: "New Club": "https://www.samsclub.com/club/new-club-az"
    "Tempe": "https://www.samsclub.com/club/4956-tempe-az"
}

# Known addresses for clubs (can be manually updated)
KNOWN_ADDRESSES = {
    "Avondale": "Avondale, AZ",
    "Bullhead City": "Bullhead City, AZ", 
    "Chandler": "Chandler, AZ",
    "Flagstaff": "Flagstaff, AZ",
    "Gilbert (1)": "Gilbert, AZ",
    "Gilbert (2)": "Gilbert, AZ",
    "Glendale": "Glendale, AZ",
    "Phoenix (1)": "Phoenix, AZ",
    "Phoenix (2)": "Phoenix, AZ",
    "Surprise": "Surprise, AZ",
    "Tempe": "Tempe, AZ",
    "Tucson": "Tucson, AZ",
    "Yuma": "Yuma, AZ",
}

# Database file for storing comprehensive history
DB_FILE = "sams_club_history.db"

def init_database():
    """Initialize SQLite database for storing comprehensive history"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create tables for comprehensive data storage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            address TEXT,
            club_url TEXT,
            fuel_url TEXT,
            created_date TEXT,
            last_updated TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_name TEXT NOT NULL,
            fuel_type TEXT NOT NULL,
            price TEXT NOT NULL,
            scraped_date TEXT NOT NULL,
            scraped_time TEXT NOT NULL,
            source TEXT DEFAULT 'scraped',
            FOREIGN KEY (club_name) REFERENCES clubs (name)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraping_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_name TEXT NOT NULL,
            scraped_date TEXT NOT NULL,
            scraped_time TEXT NOT NULL,
            success BOOLEAN,
            error_message TEXT,
            prices_found INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_FILE}")

def get_today_date():
    """Get today's date as string"""
    return date.today().isoformat()

def get_current_time():
    """Get current time as string"""
    return datetime.now().strftime("%H:%M:%S")

def check_if_scraped_today(club_name: str) -> bool:
    """Check if a club was already scraped today"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    today = get_today_date()
    cursor.execute('''
        SELECT COUNT(*) FROM scraping_log 
        WHERE club_name = ? AND scraped_date = ?
    ''', (club_name, today))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0

def check_if_all_scraped_today() -> bool:
    """Check if all locations were already scraped today"""
    all_clubs = {**locations, **ADDITIONAL_CLUBS}
    
    for club_name in all_clubs.keys():
        if not check_if_scraped_today(club_name):
            return False
    
    return True

def log_scraping_attempt(club_name: str, success: bool, error_message: str = None, prices_found: int = 0):
    """Log a scraping attempt to the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    today = get_today_date()
    current_time = get_current_time()
    
    cursor.execute('''
        INSERT INTO scraping_log (club_name, scraped_date, scraped_time, success, error_message, prices_found)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (club_name, today, current_time, success, error_message, prices_found))
    
    conn.commit()
    conn.close()

def save_club_info(club_info: Dict):
    """Save or update club information in the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    today = get_today_date()
    current_time = get_current_time()
    
    # Check if club exists
    cursor.execute('SELECT id FROM clubs WHERE name = ?', (club_info['name'],))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing club
        cursor.execute('''
            UPDATE clubs 
            SET address = ?, club_url = ?, fuel_url = ?, last_updated = ?
            WHERE name = ?
        ''', (club_info['address'], club_info['club_url'], club_info['fuel_url'], 
               f"{today} {current_time}", club_info['name']))
    else:
        # Insert new club
        cursor.execute('''
            INSERT INTO clubs (name, address, club_url, fuel_url, created_date, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (club_info['name'], club_info['address'], club_info['club_url'], 
               club_info['fuel_url'], f"{today} {current_time}", f"{today} {current_time}"))
    
    conn.commit()
    conn.close()

def save_price_data(club_name: str, prices: List[Tuple[str, str]]):
    """Save price data to the database with timestamp"""
    if not prices:
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    today = get_today_date()
    current_time = get_current_time()
    
    for fuel_type, price in prices:
        if fuel_type not in ["Error", "No prices found", "Unknown", "No prices available"]:
            cursor.execute('''
                INSERT INTO price_history (club_name, fuel_type, price, scraped_date, scraped_time, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (club_name, fuel_type, price, today, current_time, 'scraped'))
    
    conn.commit()
    conn.close()

def get_latest_prices(club_name: str) -> List[Tuple[str, str]]:
    """Get the most recent prices for a club from the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT fuel_type, price FROM price_history 
        WHERE club_name = ? 
        ORDER BY scraped_date DESC, scraped_time DESC
        LIMIT 10
    ''', (club_name,))
    
    # Group by fuel type and get the latest price for each
    latest_prices = {}
    for fuel_type, price in cursor.fetchall():
        if fuel_type not in latest_prices:
            latest_prices[fuel_type] = price
    
    conn.close()
    
    return list(latest_prices.items())

def get_price_history(club_name: str = None, days: int = 30) -> pd.DataFrame:
    """Get price history for analysis"""
    conn = sqlite3.connect(DB_FILE)
    
    if club_name:
        query = '''
            SELECT club_name, fuel_type, price, scraped_date, scraped_time
            FROM price_history 
            WHERE club_name = ? AND scraped_date >= date('now', '-{} days')
            ORDER BY scraped_date DESC, scraped_time DESC
        '''.format(days)
        df = pd.read_sql_query(query, conn, params=(club_name,))
    else:
        query = '''
            SELECT club_name, fuel_type, price, scraped_date, scraped_time
            FROM price_history 
            WHERE scraped_date >= date('now', '-{} days')
            ORDER BY scraped_date DESC, scraped_time DESC
        '''.format(days)
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df

def get_scraping_stats() -> Dict:
    """Get statistics about scraping activity"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get today's stats
    today = get_today_date()
    cursor.execute('''
        SELECT COUNT(*) as total_attempts,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
               SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
        FROM scraping_log 
        WHERE scraped_date = ?
    ''', (today,))
    
    today_stats = cursor.fetchone()
    
    # Get total clubs scraped today
    cursor.execute('''
        SELECT COUNT(DISTINCT club_name) FROM scraping_log 
        WHERE scraped_date = ?
    ''', (today,))
    
    clubs_scraped_today = cursor.fetchone()[0]
    
    # Get total clubs
    total_clubs = len({**locations, **ADDITIONAL_CLUBS})
    
    conn.close()
    
    return {
        'total_attempts_today': today_stats[0] or 0,
        'successful_today': today_stats[1] or 0,
        'failed_today': today_stats[2] or 0,
        'clubs_scraped_today': clubs_scraped_today,
        'total_clubs': total_clubs,
        'all_scraped_today': clubs_scraped_today == total_clubs
    }

def export_historical_data(days: int = 30, filename: str = None) -> str:
    """Export historical price data to CSV"""
    if filename is None:
        filename = f"sams_club_history_{days}_days.csv"
    
    df = get_price_history(days=days)
    
    if df.empty:
        print(f"No historical data found for the last {days} days.")
        return ""
    
    # Export to CSV
    df.to_csv(filename, index=False)
    print(f"Historical data exported to {filename}")
    print(f"Total entries: {len(df)}")
    print(f"Date range: {df['scraped_date'].min()} to {df['scraped_date'].max()}")
    
    return filename

def get_price_trends(club_name: str = None, days: int = 7) -> Dict:
    """Get price trends for analysis"""
    df = get_price_history(club_name, days)
    
    if df.empty:
        return {}

    trends = {}
    
    # Group by fuel type and analyze trends
    for fuel_type in df['fuel_type'].unique():
        fuel_data = df[df['fuel_type'] == fuel_type]
        
        if len(fuel_data) > 1:
            # Convert prices to numeric for analysis
            prices = []
            for price_str in fuel_data['price']:
                try:
                    price_val = float(price_str.replace('$', '').replace(',', ''))
                    prices.append(price_val)
                except ValueError:
                    continue
            
            if prices:
                trends[fuel_type] = {
                    'current': prices[0],
                    'lowest': min(prices),
                    'highest': max(prices),
                    'average': sum(prices) / len(prices),
                    'data_points': len(prices)
                }
    
    return trends

def get_headers() -> Dict[str, str]:
    """Get minimal headers - sometimes simpler is better"""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }

def fetch_html(url: str, retries: int = 1) -> Optional[BeautifulSoup]:
    """Fetch HTML with minimal approach - no fancy headers, just basic requests"""
    for attempt in range(retries):
        try:
            # Use minimal headers, no user agent
            headers = get_headers()
            resp = requests.get(url, timeout=15, headers=headers)
            resp.raise_for_status()
            
            # Check if we got a bot protection page
            if 'robot' in resp.text.lower() or 'captcha' in resp.text.lower():
                print(f"Bot protection detected on {url}")
                return None
            
            return BeautifulSoup(resp.text, 'html.parser')
            
        except requests.exceptions.Timeout:
            print(f"Couldn't fetch {url}: Timeout")
        except requests.exceptions.RequestException as e:
            print(f"Couldn't fetch {url}: {e}")
        except Exception as e:
            print(f"Couldn't fetch {url}: Unexpected error - {e}")
        
        if attempt < retries - 1:
            time.sleep(1)  # Simple delay
    
    return None

def get_club_info(club_url: str, club_name: str) -> Dict[str, str]:
    """Extract club information from club page or use known data"""
    # Try to get live data first
    soup = fetch_html(club_url)
    if soup:
        try:
            # Try to get address from various selectors
            address = KNOWN_ADDRESSES.get(club_name, "NAN")
            address_selectors = [
                "address",
                "[data-testid*='address']",
                ".club-address",
                ".address",
                "[class*='address']"
            ]
            
            for selector in address_selectors:
                addr_elem = soup.select_one(selector)
                if addr_elem:
                    address = addr_elem.get_text(strip=True)
                    break
            
            # If no structured address found, look for address-like text
            if address == "NAN":
                text = soup.get_text()
                # Look for patterns like "City, State ZIP"
                address_pattern = r'([A-Z][a-z]+(?:[\s,]+[A-Z][a-z]+)*,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)'
                addr_match = re.search(address_pattern, text)
                if addr_match:
                    address = addr_match.group(1)
            
            return {
                "name": club_name,
                "address": address,
                "club_url": club_url
            }
            
        except Exception as e:
            print(f"Error parsing club info from {club_url}: {e}")
    
    # Fallback to known data
    return {
        "name": club_name,
        "address": KNOWN_ADDRESSES.get(club_name, "NAN"),
        "club_url": club_url
    }

def get_fuel_link(club_url: str) -> Optional[str]:
    """Get fuel center link from club page or construct it"""
    soup = fetch_html(club_url)
    if soup:
        # Try multiple selectors for fuel center link
        fuel_selectors = [
            "a[href*='fuel-center']",
            "a[href*='fuel']",
            "a:contains('Fuel Center')",
            "a:contains('Fuel')"
        ]
        
        for selector in fuel_selectors:
            try:
                if "contains" in selector:
                    if "Fuel Center" in selector:
                        fuel_link = soup.find("a", string=lambda text: text and "Fuel Center" in text)
                    else:
                        fuel_link = soup.find("a", string=lambda text: text and "Fuel" in text)
                else:
                    fuel_link = soup.select_one(selector)
                
                if fuel_link and fuel_link.get("href"):
                    href = fuel_link["href"]
                    if href.startswith("/"):
                        return BASE_URL + href
                    elif href.startswith("http"):
                        return href
                    else:
                        return BASE_URL + "/" + href
            except:
                continue
    
    # Fallback: construct fuel center URL
    if "/club/" in club_url:
        return club_url + "/fuel-center"
    
    return None

def get_gas_prices(url: str) -> List[Tuple[str, str]]:
    """Extract gas prices using minimal approach - no fancy headers"""
    try:
        # Use minimal headers, no user agent
        headers = get_headers()
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        prices = []
        # Use the exact selector that worked in the original script
        for card in soup.find_all("div", class_="pa3 br3 flex-grow-1"):
            try:
                fuel_type = card.find("div", class_="tc f6 fw4 lh-title").get_text(strip=True)
                price = card.find("div", class_="flex items-center justify-center f2 fw5").get_text(strip=True)
                if fuel_type and price:
                    prices.append((fuel_type, price))
            except Exception as e:
                print(f"Error parsing price card: {e}")
                continue
        
        # If the original method didn't work, try fallback methods
        if not prices:
            print(f"Original price extraction failed for {url}, trying fallback methods...")
            prices = get_gas_prices_fallback(soup)
        
        return prices if prices else [("No prices found", "NAN")]
        
    except Exception as e:
        print(f"Couldn't fetch {url}: {e}")
        return [("Error", str(e))]

def get_gas_prices_fallback(soup: BeautifulSoup) -> List[Tuple[str, str]]:
    """Fallback method for extracting gas prices when original method fails"""
    prices = []
    try:
        # Try multiple selectors for price extraction
        price_selectors = [
            "div[class*='pa3'][class*='br3']",
            ".fuel-price-card",
            "[data-testid*='price']",
            ".price",
            "[class*='price']"
        ]
        
        for selector in price_selectors:
            cards = soup.select(selector)
            if cards:
                for card in cards:
                    try:
                        # Try different price element selectors
                        price_selectors_inner = [
                            "[class*='f2'][class*='fw5']",
                            ".price-value",
                            "[class*='price']"
                        ]
                        
                        fuel_type = "Unknown"
                        price = "NAN"
                        
                        # Try to get fuel type
                        fuel_selectors_inner = [
                            "[class*='tc'][class*='f6']",
                            ".fuel-type",
                            "[class*='fuel']"
                        ]
                        
                        for fuel_sel in fuel_selectors_inner:
                            fuel_elem = card.select_one(fuel_sel)
                            if fuel_elem:
                                fuel_type = fuel_elem.get_text(strip=True)
                                break
                        
                        # Try to get price
                        for price_sel in price_selectors_inner:
                            price_elem = card.select_one(price_sel)
                            if price_elem:
                                price = price_elem.get_text(strip=True)
                                break
                        
                        if fuel_type and price and price != "NAN":
                            prices.append((fuel_type, price))
                            
                    except Exception as e:
                        print(f"Error parsing price card: {e}")
                        continue
                break
        
        if not prices:
            # Final fallback: look for any price-like patterns in the entire page
            text = soup.get_text()
            price_pattern = r'(\$[\d,]+\.?\d*)'
            prices = [("Unknown", price) for price in re.findall(price_pattern, text)]
            
    except Exception as e:
        print(f"Error in fallback price extraction: {e}")
    
    return prices

def add_new_club(name: str, url: str) -> None:
    """Add a new club to the additional clubs dictionary"""
    global ADDITIONAL_CLUBS
    ADDITIONAL_CLUBS[name] = url
    print(f"Added new club: {name} -> {url}")

def update_known_address(club_name: str, address: str) -> None:
    """Update the known address for a club"""
    global KNOWN_ADDRESSES
    KNOWN_ADDRESSES[club_name] = address
    print(f"Updated address for {club_name}: {address}")

def add_manual_prices(club_name: str, fuel_type: str, price: str) -> None:
    """Add manual price data for a club to the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    today = get_today_date()
    current_time = get_current_time()
    
    # Insert manual price with 'manual' source
    cursor.execute('''
        INSERT INTO price_history (club_name, fuel_type, price, scraped_date, scraped_time, source)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (club_name, fuel_type, price, today, current_time, 'manual'))
    
    conn.commit()
    conn.close()
    print(f"Added manual price for {club_name}: {fuel_type} - {price}")

def show_todays_data():
    """Display today's data from the database"""
    today = get_today_date()
    
    # Get today's prices
    df = get_price_history(days=1)
    
    if df.empty:
        print("No data found for today.")
        return
    
    # Group by club and show latest prices
    clubs_data = {}
    for _, row in df.iterrows():
        club_name = row['club_name']
        if club_name not in clubs_data:
            clubs_data[club_name] = []
        clubs_data[club_name].append((row['fuel_type'], row['price'], row['scraped_time']))
    
    # Display organized by club
    for club_name, prices in clubs_data.items():
        print(f"\n{club_name}:")
        for fuel_type, price, time_str in prices:
            print(f"  {fuel_type}: {price} (at {time_str})")
    
    # Show summary
    print(f"\nTotal price entries today: {len(df)}")
    print(f"Clubs with data today: {len(clubs_data)}")

def scrape_all_clubs() -> List[Dict[str, str]]:
    """Scrape all clubs using smart approach - only scrape if not already done today"""
    print("Using smart scraping approach: only scrape locations not scraped today...")
    
    all_clubs = []
    all_locations = {**locations, **ADDITIONAL_CLUBS}
    total_clubs = len(all_locations)
    
    # Check scraping stats
    stats = get_scraping_stats()
    print(f"Today's scraping status: {stats['clubs_scraped_today']}/{stats['total_clubs']} clubs scraped")
    
    for i, (name, url) in enumerate(all_locations.items(), 1):
        print(f"Processing club {i}/{total_clubs}: {name}")
        
        # Check if already scraped today
        if check_if_scraped_today(name):
            print(f"  {name} already scraped today, using cached data")
            # Get latest prices from database
            prices = get_latest_prices(name)
            if not prices:
                prices = [("No cached prices", "NAN")]
            
            # Get club info from database or use defaults
            club_info = {
                "name": name,
                "address": KNOWN_ADDRESSES.get(name, "NAN"),
                "club_url": url,
                "fuel_url": "Cached data",
                "prices": prices
            }
            
            all_clubs.append(club_info)
            continue
        
        # Need to scrape this club
        print(f"  Scraping {name} (not scraped today)")
        
        # Get club information
        club_info = get_club_info(url, name)
        
        # Get fuel center URL
        print(f"  Getting fuel info for: {name}")
        fuel_url = get_fuel_link(url)
        club_info["fuel_url"] = fuel_url if fuel_url else "No Fuel Center"
        
        # Try to get live prices
        prices = []
        success = False
        error_message = None
        
        if fuel_url and fuel_url != "No Fuel Center":
            print(f"  Getting gas prices from: {fuel_url}")
            prices = get_gas_prices(fuel_url)
        else:
            # Try to get prices directly from club URL as fallback
            print(f"  Trying to get prices directly from club page")
            prices = get_gas_prices(url)
        
        # Check if we got valid prices
        if prices and not (len(prices) == 1 and prices[0][0] in ["Error", "No prices found"]):
            success = True
            prices_found = len(prices)
            print(f"  Successfully scraped {prices_found} prices for {name}")
        else:
            success = False
            error_message = "No valid prices found"
            prices_found = 0
            print(f"  Failed to get prices for {name}")
            # Use any cached prices as fallback
            cached_prices = get_latest_prices(name)
            if cached_prices:
                prices = cached_prices
                print(f"  Using cached prices as fallback")
            else:
                prices = [("No prices available", "NAN")]
        
        # Log the scraping attempt
        log_scraping_attempt(name, success, error_message, prices_found)
        
        # Save club info and prices to database
        save_club_info(club_info)
        save_price_data(name, prices)
        
        club_info["prices"] = prices
        all_clubs.append(club_info)
        
        # Add delay to avoid overwhelming the server
        time.sleep(random.uniform(0.5, 1.5))
    
    return all_clubs

def identify_lowest_prices(clubs_data: List[Dict]) -> Dict[str, Dict]:
    """Identify lowest prices for each fuel category"""
    price_categories = {}
    
    for club in clubs_data:
        if "prices" in club and club["prices"]:
            for fuel_type, price in club["prices"]:
                if fuel_type not in ["Error", "No prices found", "Unknown", "No prices available"]:
                    try:
                        # Extract numeric price value
                        price_value = float(price.replace('$', '').replace(',', ''))
                        
                        if fuel_type not in price_categories:
                            price_categories[fuel_type] = {"price": price_value, "club": club["name"], "address": club["address"]}
                        elif price_value < price_categories[fuel_type]["price"]:
                            price_categories[fuel_type] = {"price": price_value, "club": club["name"], "address": club["address"]}
                    except ValueError:
                        continue
    
    return price_categories

def main():
    """Main execution function"""
    print("=" * 60)
    print("Sam's Club Gas Price Scraper with Smart History Management")
    print("=" * 60)
    
    # Initialize database
    init_database()

    # Check if all locations were scraped today
    if check_if_all_scraped_today():
        print("All locations were already scraped today. Skipping scraping.")
        print("You can manually add new clubs or update addresses.")
        print("To force scraping, delete the 'sams_club_history.db' file.")
        
        # Show today's data from database
        print("\n" + "=" * 60)
        print("TODAY'S DATA (FROM DATABASE)")
        print("=" * 60)
        show_todays_data()
        return

    # Scrape all clubs using smart approach
    clubs_data = scrape_all_clubs()
    
    if not clubs_data:
        print("No club data found. Exiting.")
        return
    
    # Create DataFrame with expanded price information
    expanded_data = []
    for club in clubs_data:
        if club["prices"]:
            for fuel_type, price in club["prices"]:
                expanded_data.append({
                    "Club Name": club["name"],
                    "Address": club["address"],
                    "Club URL": club["club_url"],
                    "Fuel Center URL": club["fuel_url"],
                    "Fuel Type": fuel_type,
                    "Price": price
                })
        else:
            expanded_data.append({
                "Club Name": club["name"],
                "Address": club["address"],
                "Club URL": club["club_url"],
                "Fuel Center URL": club["fuel_url"],
                "Fuel Type": "N/A",
                "Price": "N/A"
            })
    
    # Create and display DataFrame
    df = pd.DataFrame(expanded_data)
    print("\n" + "=" * 60)
    print("ALL CLUB INFORMATION")
    print("=" * 60)
    print(df.to_string(index=False))
    
    # Identify and display lowest prices
    lowest_prices = identify_lowest_prices(clubs_data)
    if lowest_prices:
        print("\n" + "=" * 60)
        print("LOWEST PRICES BY FUEL TYPE")
        print("=" * 60)
        for fuel_type, info in lowest_prices.items():
            print(f"{fuel_type}: ${info['price']:.3f} at {info['club']} ({info['address']})")
    
    # Save results
    df.to_csv("sams_az_clubs_detailed.csv", index=False)
    print(f"\nSaved detailed results to sams_az_clubs_detailed.csv")
    
    # Show scraping statistics
    stats = get_scraping_stats()
    print(f"\n" + "=" * 60)
    print("SCRAPING STATISTICS")
    print("=" * 60)
    print(f"Total attempts today: {stats['total_attempts_today']}")
    print(f"Successful today: {stats['successful_today']}")
    print(f"Failed today: {stats['failed_today']}")
    print(f"Clubs scraped today: {stats['clubs_scraped_today']}/{stats['total_clubs']}")
    
    # Summary statistics
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total clubs processed: {len(clubs_data)}")
    print(f"Clubs with fuel centers: {len([c for c in clubs_data if c['fuel_url'] != 'No Fuel Center'])}")
    print(f"Total price entries: {len(expanded_data)}")
    
    # Interactive mode for adding new clubs and data
    print("\n" + "=" * 60)
    print("MANUAL DATA MANAGEMENT")
    print("=" * 60)
    print("To add a new club: add_new_club('Club Name', 'Club URL')")
    print("To update an address: update_known_address('Club Name', 'New Address')")
    print("To add manual prices: add_manual_prices('Club Name', 'Fuel Type', 'Price')")
    print("To view price history: get_price_history('Club Name', days=30)")
    print("To view scraping stats: get_scraping_stats()")
    print("\nExamples:")
    print("  add_new_club('Test Club', 'https://www.samsclub.com/club/test-club-az')")
    print("  update_known_address('Avondale', '123 Main St, Avondale, AZ 85323')")
    print("  add_manual_prices('Avondale', 'Regular', '$3.45')")
    print("  get_price_history('Avondale', 7)  # Last 7 days")
    print("\nNote: Using smart scraping - only scrapes locations not scraped today.")

if __name__ == "__main__":
    main()
