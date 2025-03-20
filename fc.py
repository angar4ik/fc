#!/usr/bin/env python3
import os
import json
from datetime import datetime
import argparse
from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup
import sys
from lib.fc_listing import ListingScrapper
from lib.parse_data import ParseData

COUNTIES = {
    #"POLK": "https://polk.realforeclose.com",
    "SEMINOLE": "https://seminole.realforeclose.com",
    #"MARION": "https://www.marion.realforeclose.com",
    #"VOLUSIA": "https://www.volusia.realforeclose.com",
    "ORANGE": "https://www.myorangeclerk.realforeclose.com"
}

CURRENT_COUNTY = None
BASE_URL = None
SESSION = None
NEXT_MNTH = False  # Global variable to store the --next flag value
FORCE = False # Global variable to store the --force flag value

def prompt_for_county():
    global CURRENT_COUNTY
    global BASE_URL
    """Ask the user to select a county from available options"""
    print("Available counties:")
    for i, county in enumerate(COUNTIES.keys(), 1):
        print(f"{i}. {county}")
    # Add ALL option at the end
    print(f"{len(COUNTIES) + 1}. ALL")
    
    while True:
        try:
            selection = input("\nSelect a county (enter the number): ")
            idx = int(selection) - 1
            if 0 <= idx < len(COUNTIES):
                county = list(COUNTIES.keys())[idx]
                CURRENT_COUNTY = county
                BASE_URL = COUNTIES[county]
                return
            elif idx == len(COUNTIES):
                # ALL option selected
                return True  # Return True to indicate ALL counties were selected
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def scrape_foreclosure_dates(url):
    """Scrape foreclosure dates from the provided URL."""
    try:
        global SESSION
        SESSION = HTMLSession()
        # Send request to the website
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = SESSION.get(url, headers=headers)
        response.raise_for_status()
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the dates in the calendar
        # This selector might need adjustment based on the actual structure of the website
        calendar_dates = []
        calendar_root = soup.select_one('div.CALDAYBOX')
        # Look for date elements (typically in a calendar view)
        caldaybox_elements = calendar_root.select('div.CALBOX')
        if caldaybox_elements:
            for element in caldaybox_elements:
                # Extract the dayid attribute from the div
                day_id = element.get('dayid')
                active = element.select_one('span.CALMSG span.CALACT')
                if day_id and active:
                    calendar_dates.append(day_id)
                    
        return calendar_dates
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error during scraping: {e}", file=sys.stderr)
        return []

def get_date_specific_url(date):
    """
    Generate URL for a specific date.
    """
    return f"{BASE_URL}/index.cfm?zaction=AUCTION&Zmethod=PREVIEW&AUCTIONDATE={date}"

def save_data_to_file(date, auction_items, url):
    # Create data directory if it doesn't exist
    os.makedirs(f'data/{CURRENT_COUNTY}', exist_ok=True)
    safe_date = date.replace('/', '_')
    # Format date for filename
    filename = f"data/{CURRENT_COUNTY}/{safe_date}.json"

    # Create a dictionary with metadata and auction items
    data_to_save = {
        "url": url,
        "scrape_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "auction_items": auction_items
    }
    
    # Save auction items to file
    with open(filename, 'w') as f:
        json.dump(data_to_save, f, indent=4, default=str)
    
    print(f"Data saved to {filename}")

def process_county(county=None):
    global CURRENT_COUNTY, BASE_URL, SESSION, NEXT_MNTH, FORCE
    
    if county:
        CURRENT_COUNTY = county
        BASE_URL = COUNTIES[county]
        SESSION = None
    # Get the current date and calculate next month's date if NEXTMNT is True
    if NEXT_MNTH:
        # Import required modules for date manipulation
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        # Get current date
        current_date = datetime.now()
        # Add one month to get next month
        next_month_date = current_date + relativedelta(months=1)
        # Format the date as MM/01/YYYY (first day of next month)
        formatted_date = next_month_date.strftime("%m/01/%Y")
        # Generate URL with the next month's date
        #/index.cfm?zaction=user&zmethod=calendar&selCalDate=04/01/2025
        url = f"{BASE_URL}/index.cfm?zaction=USER&zmethod=CALENDAR&selCalDate={formatted_date}"
    else:
        # Use the default URL (current month)
        url = f"{BASE_URL}/index.cfm?zaction=USER&zmethod=CALENDAR"
    
    #url = f"{BASE_URL}/index.cfm?zaction=USER&zmethod=CALENDAR"
    print(f"URL: {url}")
    parse_data = ParseData()
    listing_scrapper = ListingScrapper()
    dates = scrape_foreclosure_dates(url)

    if dates:
        for date in dates:
            # Check if file already exists for this date
            filename = f"data/{CURRENT_COUNTY}/{date.replace('/', '_')}.json"
            if os.path.exists(filename) and not FORCE:
                print(f"Skipping date {date} - data already exists")
                continue
            url = get_date_specific_url(date)
            raw_data = listing_scrapper.get_data_specific_url(url, BASE_URL, SESSION)
            auction_items = parse_data.parse_auction_data(raw_data, CURRENT_COUNTY)
            print(f"Auction items: [{len(auction_items)}] at [{date}]")
            # filter from json database
            auction_items = parse_data.enrich_auction_items(auction_items)
            if auction_items:
                print("-" * 50)
                print(f"URL: {url}")
                parse_data.display_auction_items(auction_items)
                save_data_to_file(date, auction_items, url)
    else:
        print(f"No dates found for {CURRENT_COUNTY}.")

def main():
    global NEXT_MNTH, FORCE
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Foreclosure data scraper')
    parser.add_argument('--next', action='store_true', help='Flag for next month processing')
    parser.add_argument('--force', action='store_true', help='Force processing even if data already exists')
    args = parser.parse_args()
    # Store the --next flag value in the global variable
    NEXT_MNTH = args.next
    FORCE = args.force

    process_all = prompt_for_county()
    
    if process_all:
        print("Processing ALL counties...")
        for county in COUNTIES.keys():
            print(f"\n{'=' * 30}")
            print(f"Processing {county} county")
            print(f"{'=' * 30}")
            process_county(county)
    else:
        # Process only the selected county
        process_county()

if __name__ == "__main__":
    main()