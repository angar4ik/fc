#!/usr/bin/env python3

import sys
import time
import requests
from requests_html import HTMLSession

class ListingScrapper:

    def get_data_specific_url(self, url, base_url, session):
        """Scrape foreclosure dates from the provided URL."""
        try:
            # Add headers to mimic Chrome browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = session.get(url, headers=headers)
            
            # This will execute JavaScript on the page
            response.html.render()

            timestamp1 = int(time.time() * 1000)
            timestamp2 = timestamp1 + 451

            #ajax_url = f"https://polk.realforeclose.com/index.cfm?zaction=AUCTION&ZMETHOD=UPDATE&FNC=UPDATE&ref={ref_ids},&tx={timestamp1}&_={timestamp2}"
            ajax_url = f"{base_url}/index.cfm?zaction=AUCTION&Zmethod=UPDATE&FNC=LOAD&AREA=W&PageDir=0&doR=1&tx={timestamp1}&bypassPage=1&test=1&_={timestamp2}"
            
            # Make the AJAX request
            ajax_response = session.get(ajax_url)
            #print(f"ajax_response: {ajax_response.text.strip()}")
            
            return ajax_response.text.strip()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the webpage: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Error during scraping: {e}", file=sys.stderr)
                        
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the webpage: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Error during scraping: {e}", file=sys.stderr)
            return []

# # This should be outside the class definition
# if __name__ == "__main__":
#     # Create an instance of ListingScrapper
#     scrapper = ListingScrapper()
    
#     # Create a session object using requests_html.HTMLSession
#     session = HTMLSession()
    
#     # URL to scrape - replace with the actual URL you want to scrape
#     url = "https://www.marion.realforeclose.com/index.cfm?zaction=AUCTION&Zmethod=PREVIEW&AUCTIONDATE=03/03/2025"
    
#     # Call the method and print the result
#     result = scrapper.get_data_specific_url(url, "", session)
#     print(result)