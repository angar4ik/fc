#!/usr/bin/env python3

import argparse
import json
from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup
import sys

import urllib.parse

BASE_URL = "https://www.realtor.com/"
SESSION = None
class RealtorData:
    """Scrape realtor.com for foreclosure listings."""
    def scrape_suggests(self, address):
        try:
            global SESSION
            SESSION = HTMLSession()
            # Send request to the website
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = SESSION.get(f"https://parser-external.geo.moveaws.com/suggest?input={urllib.parse.quote(address, safe='')}&client_id=rdc-home&limit=10&area_types=address%2Cneighborhood%2Ccity%2Ccounty%2Cpostal_code%2Cstreet%2Cschool%2Cschool_district%2Cuniversity%2Cpark%2Cstate%2Cmlsid&lat=-1&long=-1", headers=headers)
            response.raise_for_status()
            # Parse the HTML content
            soup2 = BeautifulSoup(response.text, 'html.parser')
            return soup2.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the webpage: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Error during scraping: {e}", file=sys.stderr)
            return []

    def extract_property_id(self, json_string):
        """Extract the property ID from the JSON response."""
        try:
            data = json.loads(json_string)
            first_element = data["autocomplete"][0]
            full_id = first_element["_id"]
            # Remove the 'addr:' prefix if present
            if full_id.startswith("addr:"):
                return full_id.replace("addr:", "")
            return full_id
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            #print(f"Error extracting property ID: {e}", file=sys.stderr)
            return None

    def get_property_address(self, address):
        raw = self.scrape_suggests(address)
        id = self.extract_property_id(raw)
        if id is None:
            return None
        url = f"https://www.realtor.com/realestateandhomes-detail/M{id}"
        return url