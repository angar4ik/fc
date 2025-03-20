import json
import re
from typing import List, Dict, Any
from lib.realtor_data import RealtorData

class ParseData:
    def parse_auction_data(self, raw_data: str, county: str = "default") -> List[Dict[str, Any]]:
        """
        Parse raw auction data and extract important information
        
        Args:
            raw_data: Raw JSON string containing auction data
        
        Returns:
            List of dictionaries containing structured auction information
        """
        # Parse the JSON
        try:
            data = json.loads(raw_data)
            html_content = data.get("retHTML", "")
            auction_ids = data.get("rlist", "").split(",")
            if not auction_ids:
                return []

        except json.JSONDecodeError:
            print("Error: Invalid JSON data")
            return []
        
        # Find all auction items
        auction_items = []
        
        for auction_id in auction_ids:
            # Find the div with the specific ID
            pattern = rf'<div id=\"AITEM_{auction_id}\".*?@E_ITEM_SPACER\">&nbsp;'
            match = re.search(pattern, html_content, re.DOTALL)
            
            if not match:
                continue
                
            item_html = match.group(0)
            
            if county.lower() == "orange":
                auction_info = self.parse_orange_county_item(item_html, auction_id)
            else:
                auction_info = self.parse_default_item(item_html, auction_id)
            
            auction_items.append(auction_info)
        
        return auction_items

    def parse_default_item(self, item_html: str, auction_id: str) -> Dict[str, Any]:
        """Parse auction item using default format"""
        auction_info = {
            "auction_id": auction_id,
            "auction_type": self.extract_field(item_html, "Auction Type:", "@CAD_DTA\">", "@G"),
            "case_number": self.extract_field(item_html, "Case #:", "@CAD_DTA\">", "@G").strip(),
            "final_judgment_amount": self.extract_field(item_html, "Final Judgment Amount:", "@CAD_DTA\">", "@G"),
            "parcel_id": self.extract_field(item_html, "Parcel ID:", "@CAD_DTA\">", "@G").strip(),
            "property_address": self.extract_property_address(item_html),
            "assessed_value": self.extract_field(item_html, "Assessed Value:", "@CAD_DTA\">", "@G"),
            "plaintiff_max_bid": self.extract_field(item_html, "Plaintiff Max Bid:", "@CAD_DTA ASTAT_MSGPB\">", "@G")
        }
        
        # Clean up case number and parcel ID (remove HTML tags)
        auction_info["case_number"] = re.sub(r'<.*?>', '', auction_info["case_number"]).strip()
        auction_info["parcel_id"] = re.sub(r'<.*?>', '', auction_info["parcel_id"]).strip()
        
        return auction_info
    
    def parse_orange_county_item(self, item_html: str, auction_id: str) -> Dict[str, Any]:
        """Parse auction item using Orange County format"""
        # Extract case number which has link inside
        case_number = self.extract_field(item_html, "Case #:", "@AAD_DTA\">", "@B")
        case_number = re.sub(r'<.*?>', '', case_number).strip()
        
        # Extract parcel ID which has link inside
        parcel_id = self.extract_field(item_html, "Parcel ID:", "@AAD_DTA\">", "@B")
        parcel_id = re.sub(r'<.*?>', '', parcel_id).strip()
        
        # Extract property address (which is in two parts in Orange County format)
        address1 = self.extract_field(item_html, "Property Address:", "@CAD_DTA\">", "@B").strip()
        
        # Try to find the city and zip
        city_zip_pattern = r'@CAD_LBL\"[^>]*>@B<div tabindex=\"0\"@CAD_DTA\">(.*?), (\d+)@B'
        city_zip_match = re.search(city_zip_pattern, item_html)
        
        if city_zip_match:
            city = city_zip_match.group(1).strip()
            zip_code = city_zip_match.group(2).strip()
            property_address = f"{address1}, {city}, FL {zip_code}"
        else:
            property_address = address1
        
        auction_info = {
            "auction_id": auction_id,
            "case_number": case_number,
            "final_judgment_amount": self.extract_field(item_html, "Final Judgment Amount:", "@CAD_DTA\">", "@B"),
            "parcel_id": parcel_id,
            "property_address": property_address,
            "assessed_value": self.extract_field(item_html, "Assessed Value:", "@CAD_DTA\">", "@B"),
            "plaintiff_max_bid": self.extract_field(item_html, "Plaintiff Max Bid:", "@CAD_DTA ASTAT_MSGPB\">", "@B")
        }
        
        return auction_info
    
    def extract_field(self, html: str, field_label: str, start_marker: str, end_marker: str) -> str:
        """Extract a specific field from the HTML-like content"""
        pattern = rf'{field_label}.*?{start_marker}(.*?){end_marker}'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def extract_property_address(self, html: str) -> str:
        """Extract and combine property address parts"""
        address1 = self.extract_field(html, "Property Address:", "@CAD_DTA\">", "@G")
        
        # Find the city, state, zip part - it's in a different format
        pattern = r'@CAD_LBL\" scope=\"row\">@F tabindex=\"0\" @CAD_DTA\">(.*?), FL-\s*(\d+)@G'
        match = re.search(pattern, html)
        
        if match:
            city = match.group(1).strip()
            zip_code = match.group(2).strip()
            return f"{address1}, {city}, FL-{zip_code}"
        
        return address1
    
    def display_auction_items(self, auction_items: List[Dict[str, Any]]) -> None:
        realtor_data = RealtorData()
        """Print auction items in a readable format"""
        for i, item in enumerate(auction_items, 1):
            # print(f"\nProperty {i} (ID: {item['auction_id']})")
            print("." * 25)
            print(f"Case #: {item['case_number']}")
            print(f"Parcel ID: {item['parcel_id']}")
            print(f"Final Judgment Amount: {item['final_judgment_amount']}")
            print(f"Assessed Value: {item['assessed_value']}")
            print(f"Property Address: {item['property_address']}")

    def parse_and_display_auction_data(self, raw_data):
        # Example usage
        auction_items = self.parse_auction_data(raw_data)
        # Display count before filtering
        print(f"Auction items: {len(auction_items)}")
        # Filter items based on assessed value
        auction_items = self.filter_items_by_assessed_value_min_max(auction_items, 100000, 150000)
        auction_items = self.filter_items_by_assessed_value(auction_items)

        if auction_items:
            self.display_auction_items(auction_items)

    def enrich_auction_items(self, auction_items):
        realtor_data = RealtorData()
        for item in auction_items:
            link = realtor_data.get_property_address(item['property_address'])
            if link:
                item['realtor_link'] = link
            else:
                item['realtor_link'] = None
        return auction_items

