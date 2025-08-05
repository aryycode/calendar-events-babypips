from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time

app = Flask(__name__)

class BabyPipsSeleniumScraper:
    def __init__(self):
        self.base_url = "https://www.babypips.com"
        self.calendar_url = "https://www.babypips.com/economic-calendar"
        self.months = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        
    def initialize_driver(self):
        """Initialize Chrome webdriver with optimized options"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--headless')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            print(f"Error initializing webdriver: {str(e)}")
            return None

    def interact_with_site(self, driver):
        """Interact with site to load proper calendar view"""
        try:
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Try to click week button (first xpath pattern)
            try:
                week_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/section[2]/div/div/div[1]/div/div[2]/div[2]/button[1]'))
                )
                week_button.click()
                print("Week button clicked (pattern 1)")
                
                # Set timezone if needed
                try:
                    timestamp_key = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/section[2]/div/div/div[1]/div/div[2]/div[1]/button'))
                    )
                    timestamp_key.click()
                    
                    select_timestamp = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/section[2]/div/div/div[1]/div/div[2]/div[1]/ol/li[13]/div'))
                    )
                    select_timestamp.click()
                    print("Timezone set")
                except:
                    print("Timezone setting skipped")
                    
            except:
                # Try alternative xpath pattern
                try:
                    week_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/section[2]/div/div/div[1]/div/div[2]/div[2]/button[1]'))
                    )
                    week_button.click()
                    print("Week button clicked (pattern 2)")
                    
                    # Set timezone
                    try:
                        timestamp_key = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/section[2]/div/div/div[1]/div/div[2]/div[1]/button'))
                        )
                        timestamp_key.click()
                        
                        select_timestamp = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/section[2]/div/div/div[1]/div/div[2]/div[1]/ol/li[13]/div'))
                        )
                        select_timestamp.click()
                        print("Timezone set (pattern 2)")
                    except:
                        print("Timezone setting skipped (pattern 2)")
                        
                except Exception as e:
                    print(f"Could not interact with site elements: {str(e)}")
                    
            # Wait a bit for content to load after interaction
            time.sleep(2)
            
        except Exception as e:
            print(f"Error interacting with site: {str(e)}")

    def scrape_calendar(self, year=None, week=None, currency_filter=None, impact_filter=None, max_retries=3):
        """Scrape economic calendar using Selenium"""
        
        # Use current year/week if not provided
        if not year or not week:
            current_date = datetime.now()
            year = str(current_date.year)
            week = str(current_date.isocalendar()[1])
        
        year = str(year)
        week = f"{int(week):02d}"
        url = f"{self.calendar_url}?week={year}-W{week}"
        
        print(f"Scraping: {url}")
        
        for attempt in range(max_retries):
            driver = None
            try:
                print(f"Attempt {attempt + 1}/{max_retries}")
                
                # Initialize driver
                driver = self.initialize_driver()
                if not driver:
                    continue
                
                # Load page
                driver.get(url)
                print(f"Page loaded, source length: {len(driver.page_source)}")
                
                # Check if page loaded properly
                if len(driver.page_source) < 200:
                    print("Page source too short, retrying...")
                    continue
                
                # Interact with site elements
                self.interact_with_site(driver)
                
                # Get final page source
                page_source = driver.page_source
                print(f"Final page source length: {len(page_source)}")
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(page_source, 'html.parser')
                events = self.parse_calendar_data(soup, year, week)
                
                # Apply filters
                filtered_events = self.apply_filters(events, currency_filter, impact_filter)
                
                return {
                    'success': True,
                    'total_events': len(filtered_events),
                    'events': filtered_events,
                    'filters_applied': {
                        'year': year,
                        'week': f'W{week}',
                        'currency': currency_filter,
                        'impact': impact_filter
                    },
                    'scraped_at': datetime.now().isoformat(),
                    'source': url
                }
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        'error': f'Failed to scrape after {max_retries} attempts',
                        'last_error': str(e)
                    }
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                        
        return {'error': 'Max retries exceeded'}

    def parse_calendar_data(self, soup, year, week):
        """Parse calendar data from BeautifulSoup object"""
        events = []
        
        try:
            # Look for calendar day blocks based on the GitHub example
            blocks = soup.find_all('div', class_='Section-module__container___WUPgM Table-module__day___As54H')
            print(f"Found {len(blocks)} calendar day blocks")
            
            if not blocks:
                # Fallback: look for similar structures
                blocks = soup.find_all('div', class_=re.compile(r'day', re.I)) or \
                         soup.find_all('section', class_=re.compile(r'day', re.I))
                print(f"Fallback: Found {len(blocks)} day-related blocks")
            
            for i, block in enumerate(blocks):
                try:
                    # Extract day information
                    month_elem = block.find('div', class_='Table-module__month___PGbXI')
                    day_elem = block.find('div', class_='Table-module__dayNumber___dyJpm')
                    weekday_elem = block.find('td', class_='Table-module__weekday___p3Buh')
                    
                    if not month_elem or not day_elem:
                        # Try alternative selectors
                        month_elem = block.find(string=re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'))
                        day_elem = block.find(string=re.compile(r'\d{1,2}'))
                    
                    month_name = month_elem.get_text() if hasattr(month_elem, 'get_text') else str(month_elem) if month_elem else 'Jan'
                    day_number = day_elem.get_text() if hasattr(day_elem, 'get_text') else str(day_elem) if day_elem else '1'
                    
                    # Skip December dates in week 1 (previous year)
                    if week == '01' and month_name == 'Dec':
                        continue
                    
                    month_num = self.months.get(month_name, '01')
                    
                    # Find event rows in this day block
                    event_rows = block.find_all('tr') if block.find('tbody') else []
                    if block.find('tbody'):
                        event_rows = block.find('tbody').find_all('tr')
                    
                    print(f"Day {day_number} {month_name}: Found {len(event_rows)} events")
                    
                    for row in event_rows:
                        event = self.parse_event_row(row, year, month_num, day_number)
                        if event:
                            events.append(event)
                            
                except Exception as e:
                    print(f"Error parsing day block {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing calendar data: {str(e)}")
        
        print(f"Total events parsed: {len(events)}")
        return events

    def parse_event_row(self, row, year, month_num, day_number):
        """Parse individual event row"""
        try:
            # Extract event details using the CSS classes from GitHub example
            time_elem = row.find('td', class_='Table-module__time___IHBtp')
            currency_elem = row.find('td', class_='Table-module__currency___gSAJ5')
            name_elem = row.find('td', class_='Table-module__name___FugPe')
            impact_elem = row.find('td', class_='Table-module__impact___kYuei')
            actual_elem = row.find('td', class_='Table-module__actual___kzVNq')
            forecast_elem = row.find('td', class_='Table-module__forecast___WchYX')
            previous_elem = row.find('td', class_='Table-module__previous___F0PHu')
            
            # Fallback if specific classes not found
            if not time_elem:
                cells = row.find_all('td')
                if len(cells) >= 7:
                    time_elem, currency_elem, name_elem, impact_elem, actual_elem, forecast_elem, previous_elem = cells[:7]
            
            # Extract text values
            time_val = time_elem.get_text(strip=True) if time_elem else ''
            currency_val = currency_elem.get_text(strip=True) if currency_elem else ''
            name_val = name_elem.get_text(strip=True) if name_elem else ''
            impact_val = impact_elem.get_text(strip=True) if impact_elem else ''
            actual_val = actual_elem.get_text(strip=True) if actual_elem else ''
            forecast_val = forecast_elem.get_text(strip=True) if forecast_elem else ''
            previous_val = previous_elem.get_text(strip=True) if previous_elem else ''
            
            # Skip empty rows
            if not name_val or len(name_val) < 3:
                return None
            
            # Calculate timestamp
            timestamp = self.calculate_timestamp(year, month_num, day_number, time_val)
            
            return {
                'date': f"{year}-{month_num}-{day_number.zfill(2)}",
                'time': time_val,
                'currency': currency_val,
                'event_name': name_val,
                'importance': self.normalize_impact(impact_val),
                'actual': actual_val,
                'forecast': forecast_val,
                'previous': previous_val,
                'timestamp': timestamp,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing event row: {str(e)}")
            return None

    def calculate_timestamp(self, year, month_num, day_number, time_val):
        """Calculate UTC timestamp for event"""
        try:
            if time_val == 'All Day' or not time_val:
                dt = datetime(int(year), int(month_num), int(day_number), 0, 0, 0)
            else:
                hour = int(time_val.split(':')[0]) if ':' in time_val else 0
                minute = int(time_val.split(':')[1]) if ':' in time_val and len(time_val.split(':')) > 1 else 0
                dt = datetime(int(year), int(month_num), int(day_number), hour, minute, 0)
            
            return str(int(dt.timestamp()))
        except:
            return str(int(datetime.now().timestamp()))

    def normalize_impact(self, impact_val):
        """Normalize impact level"""
        impact_lower = impact_val.lower()
        if 'high' in impact_lower or 'red' in impact_lower:
            return 'High'
        elif 'medium' in impact_lower or 'med' in impact_lower or 'blue' in impact_lower:
            return 'Medium'
        elif 'low' in impact_lower or 'gray' in impact_lower or 'grey' in impact_lower:
            return 'Low'
        else:
            return impact_val if impact_val else 'Unknown'

    def apply_filters(self, events, currency_filter, impact_filter):
        """Apply filters to events"""
        filtered_events = events
        
        if currency_filter:
            currencies = [c.upper().strip() for c in currency_filter.split(',')]
            filtered_events = [
                event for event in filtered_events 
                if any(curr in event.get('currency', '').upper() for curr in currencies)
            ]
        
        if impact_filter:
            impacts = [i.lower().strip() for i in impact_filter.split(',')]
            filtered_events = [
                event for event in filtered_events 
                if event.get('importance', '').lower() in impacts
            ]
        
        return filtered_events

# Initialize scraper
scraper = BabyPipsSeleniumScraper()

@app.route('/')
def home():
    """API documentation"""
    return jsonify({
        'message': 'BabyPips Economic Calendar Scraper API - Selenium Version',
        'version': '3.0.0',
        'endpoints': {
            '/calendar': 'GET - Scrape current week',
            '/calendar?year=2025&week=32': 'GET - Scrape specific week',
            '/calendar?currency=USD,EUR': 'GET - Filter by currencies',
            '/calendar?impact=high,medium': 'GET - Filter by impact level',
            '/weeks': 'GET - Get available weeks',
            '/health': 'GET - Health check'
        },
        'note': 'This version uses Selenium WebDriver and requires Chrome/Chromium installed',
        'examples': [
            '/calendar',
            '/calendar?year=2025&week=32',
            '/calendar?currency=USD,EUR&impact=high',
            '/calendar?year=2025&week=32&currency=USD&impact=high'
        ]
    })

@app.route('/calendar')
def get_calendar():
    """Get economic calendar data"""
    try:
        # Get parameters
        year = request.args.get('year')
        week = request.args.get('week')
        currency_filter = request.args.get('currency')
        impact_filter = request.args.get('impact')
        
        # Validate parameters
        if year and not year.isdigit():
            return jsonify({'error': 'Year must be a number'}), 400
        
        if week and (not week.isdigit() or int(week) < 1 or int(week) > 53):
            return jsonify({'error': 'Week must be a number between 1 and 53'}), 400
        
        # Scrape data
        result = scraper.scrape_calendar(year, week, currency_filter, impact_filter)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/weeks')
def get_available_weeks():
    """Get list of available weeks"""
    try:
        current_date = datetime.now()
        weeks = []
        
        for i in range(-2, 5):
            target_date = current_date + timedelta(weeks=i)
            year, week_num, _ = target_date.isocalendar()
            
            monday = target_date - timedelta(days=target_date.weekday())
            friday = monday + timedelta(days=4)
            
            weeks.append({
                'year': year,
                'week': week_num,
                'display': f"Week {week_num}, {year}",
                'date_range': f"{monday.strftime('%b %d')} - {friday.strftime('%b %d, %Y')}",
                'url': f"/calendar?year={year}&week={week_num}",
                'is_current': i == 0
            })
        
        return jsonify({
            'available_weeks': weeks,
            'current_week': f"{current_date.isocalendar()[0]}-W{current_date.isocalendar()[1]:02d}",
            'total_weeks': len(weeks)
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Error generating week list',
            'message': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test webdriver initialization
        driver = scraper.initialize_driver()
        driver_status = 'working' if driver else 'failed'
        if driver:
            driver.quit()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'webdriver_status': driver_status,
            'scraper_version': '3.0.0',
            'requirements': ['Chrome/Chromium browser', 'ChromeDriver']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'requirements': ['Chrome/Chromium browser', 'ChromeDriver']
        }), 500

if __name__ == '__main__':
    print("=" * 70)
    print("BabyPips Economic Calendar Scraper v3.0 - Selenium Version")
    print("=" * 70)
    print("⚠️  REQUIREMENTS:")
    print("   - Chrome or Chromium browser installed")
    print("   - ChromeDriver installed and in PATH")
    print("   - pip install selenium beautifulsoup4 flask")
    print()
    print("📊 Endpoints:")
    print("   - GET / - API documentation")
    print("   - GET /calendar - Scrape current week")
    print("   - GET /calendar?year=2025&week=32 - Scrape specific week")
    print("   - GET /health - Health check")
    print()
    print("Example URLs:")
    print("   http://localhost:5000/calendar")
    print("   http://localhost:5000/calendar?year=2025&week=32&currency=USD")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)