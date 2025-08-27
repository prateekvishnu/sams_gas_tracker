# Sam's Club Gas Price Scraper

A comprehensive Python application for scraping and managing gas prices from Sam's Club locations across Arizona. Features smart scraping logic, comprehensive history tracking, and data validation.

## 🚀 Features

### Core Functionality
- **Smart Scraping**: Only scrapes locations not already scraped today
- **Comprehensive History**: SQLite database storage with timestamps
- **Efficiency**: Skips scraping if all locations were already scraped today
- **Data Validation**: Ensures addresses contain correct city names
- **Error Handling**: Robust error handling with fallback to cached data

### Data Management
- **13 Arizona Locations**: Covers major cities including Phoenix, Tucson, Flagstaff, and more
- **Fuel Price Tracking**: Monitors regular, premium, and diesel prices
- **Address Validation**: Extracts and validates club addresses
- **Historical Analysis**: Price trends and analysis over time

### Smart Features
- **Daily Limits**: Prevents duplicate scraping on the same day
- **Hybrid Approach**: Live data when possible, cached data as fallback
- **Manual Updates**: Add new clubs, update addresses, and input manual prices
- **Export Options**: CSV export and detailed reports

## 📍 Supported Locations

| City | Club ID | URL |
|------|---------|------|
| Avondale | 4830 | [View](https://www.samsclub.com/club/4830-avondale-az) |
| Bullhead City | 4915 | [View](https://www.samsclub.com/club/4915-bullhead-city-az) |
| Chandler | 6213 | [View](https://www.samsclub.com/club/6213-chandler-az) |
| Flagstaff | 6604 | [View](https://www.samsclub.com/club/6604-flagstaff-az) |
| Gilbert (1) | 6605 | [View](https://www.samsclub.com/club/6605-gilbert-az) |
| Gilbert (2) | 4829 | [View](https://www.samsclub.com/club/4829-gilbert-az) |
| Glendale | 4732 | [View](https://www.samsclub.com/club/4732-glendale-az) |
| Phoenix (1) | 6606 | [View](https://www.samsclub.com/club/6606-phoenix-az) |
| Phoenix (2) | 6608 | [View](https://www.samsclub.com/club/6608-phoenix-az) |
| Surprise | 4955 | [View](https://www.samsclub.com/club/4955-surprise-az) |
| Tempe | 4956 | [View](https://www.samsclub.com/club/4956-tempe-az) |
| Tucson | 6692 | [View](https://www.samsclub.com/club/6692-tucson-az) |
| Yuma | 6205 | [View](https://www.samsclub.com/club/6205-yuma-az) |

## 🛠️ Installation

### Prerequisites
- Python 3.7+
- pip package manager

### Dependencies
```bash
pip install requests beautifulsoup4 pandas
```

### Quick Start
1. Clone or download the project files
2. Install dependencies: `pip install -r requirements.txt`
3. Run the main scraper: `python sams_gas_prices_2.py`

## 📖 Usage

### Basic Scraping
```bash
# Run the main scraper
python sams_gas_prices_2.py
```

### Testing Links and Addresses
```bash
# Test all URLs and validate addresses
python test_sams_links_independent.py
```

### Manual Data Management
```python
# Add a new club
add_new_club('New Club', 'https://www.samsclub.com/club/new-club-az')

# Update an address
update_known_address('Avondale', '123 Main St, Avondale, AZ 85323')

# Add manual prices
add_manual_prices('Avondale', 'Regular', '$3.45')

# View price history
get_price_history('Avondale', days=7)

# Export historical data
export_historical_data(days=30, filename='gas_prices_history.csv')
```

## 🔍 How It Works

### Smart Scraping Logic
1. **Daily Check**: Verifies if locations were already scraped today
2. **Selective Scraping**: Only scrapes locations not yet processed
3. **Efficiency**: Skips entire process if all locations are up-to-date
4. **Fallback**: Uses cached data when live scraping fails

### Data Flow
```
URL Check → Accessibility Test → Address Extraction → City Validation → Database Storage
    ↓              ↓                ↓                ↓              ↓
  Working?     Can Access?     Found Address?   City Match?   Save Data
```

### Database Structure
- **clubs**: Club information and metadata
- **price_history**: All price data with timestamps
- **scraping_log**: Scraping attempts and results

## 📊 Output Files

### Generated Files
- `sams_az_clubs_detailed.csv` - Main data export
- `sams_club_history.db` - SQLite database
- `validation_report_independent.txt` - Test results

### Data Format
```csv
Club Name,Address,Club URL,Fuel Center URL,Fuel Type,Price
Avondale,Avondale AZ,https://...,https://...,Regular,$3.45
Flagstaff,Flagstaff AZ,https://...,https://...,Premium,$3.89
```

## 🧪 Testing and Validation

### Link Validation
The test script validates:
- ✅ URL accessibility (HTTP 200 responses)
- ✅ Address extraction from club pages
- ✅ City name presence in addresses
- ✅ Address format validation

### Running Tests
```bash
# Comprehensive validation
python test_sams_links_independent.py

# Check specific aspects
python -c "
from test_sams_links_independent import validate_club_data
results = validate_club_data()
print(f'Success Rate: {results[\"accessible_urls\"]}/{results[\"total_clubs\"]}')
"
```

## 🔧 Configuration

### Customization Options
- **Add New Clubs**: Update `ADDITIONAL_CLUBS` dictionary
- **Modify Addresses**: Update `KNOWN_ADDRESSES` dictionary
- **Change URLs**: Update `locations` dictionary
- **Adjust Delays**: Modify sleep times in scraping functions

### Environment Variables
```bash
# Optional: Set custom timeout
export SAM_SCRAPER_TIMEOUT=20

# Optional: Set custom user agent
export SAM_SCRAPER_USER_AGENT="Custom Bot/1.0"
```

## 📈 Data Analysis

### Price Trends
```python
# Get price trends for the last 7 days
trends = get_price_trends('Avondale', days=7)

# Analyze specific fuel types
for fuel_type, data in trends.items():
    print(f"{fuel_type}: ${data['current']:.2f} (Avg: ${data['average']:.2f})")
```

### Historical Export
```python
# Export last 30 days of data
export_historical_data(days=30, filename='monthly_report.csv')

# Get specific club history
history = get_price_history('Phoenix (1)', days=14)
```

## 🚨 Troubleshooting

### Common Issues

#### Bot Protection
- **Symptoms**: "Bot protection detected" messages
- **Solution**: Wait and retry, or use manual price updates

#### Connection Errors
- **Symptoms**: Timeout or connection errors
- **Solution**: Check internet connection, increase timeout values

#### Address Extraction Failures
- **Symptoms**: "No address extracted" messages
- **Solution**: Run validation test, check if club pages changed

### Debug Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check database status
import sqlite3
conn = sqlite3.connect('sams_club_history.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM price_history")
print(f"Total price records: {cursor.fetchone()[0]}")
```

## 📝 API Reference

### Main Functions

#### `scrape_all_clubs()`
Scrapes all clubs using smart logic.

#### `get_gas_prices(url)`
Extracts gas prices from a fuel center URL.

#### `add_manual_prices(club_name, fuel_type, price)`
Adds manual price data to the database.

#### `get_price_history(club_name=None, days=30)`
Retrieves historical price data.

#### `export_historical_data(days=30, filename=None)`
Exports historical data to CSV.

### Database Functions

#### `init_database()`
Initializes the SQLite database and tables.

#### `save_price_data(club_name, prices)`
Saves price data with timestamps.

#### `get_latest_prices(club_name)`
Gets the most recent prices for a club.

## 🤝 Contributing

### Adding New Features
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### Reporting Issues
- Include error messages and stack traces
- Specify Python version and OS
- Provide sample data if possible

## 📄 License

This project is for educational and personal use. Please respect Sam's Club's terms of service and implement appropriate rate limiting.

## 🙏 Acknowledgments

- Built with Python, BeautifulSoup, and SQLite
- Designed for efficient data collection and analysis
- Special thanks to the Sam's Club community

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Run the validation tests
3. Review the database for data integrity
4. Check recent changes in club page structures

---

**Last Updated**: August 26, 2025  
**Version**: 2.0  
**Author**: Vishnu K
