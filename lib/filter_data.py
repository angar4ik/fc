import pandas as pd
import datetime
import random

class FilterData:
    def filer(self, data, min = 0, max: int = 10000000):
        filtered_items = []
        for item in data['auction_items']:
            if not item.get('assessed_value') or not item.get('final_judgment_amount'):
                continue

            try:
                # Clean currency strings by removing $ and commas
                assessed_value_str = str(item.get('assessed_value')).replace('$', '').replace(',', '')
                final_judgment_str = str(item.get('final_judgment_amount')).replace('$', '').replace(',', '')
                assessed_value = float(assessed_value_str)
                final_judgment = float(final_judgment_str)
                
                # Split conditions for clarity
                condition1 = (assessed_value > final_judgment) and (final_judgment < max)
                condition2 = (assessed_value > min) and (assessed_value < max)
                
                if condition1 and condition2:
                    item['auction_date'] = data['auction_date']
                    #print(item)
                    filtered_items.append(item)
            except (ValueError, KeyError) as e:
                # Handle cases where conversion fails or keys don't exist
                print(f"Error processing item: {e}")
        
        return filtered_items

    def save_to_excel(self, filtered_items):
        # Convert to DataFrame and save as Excel
        if filtered_items:
            # Flatten the list if it contains nested lists
            flat_items = []
            for item_list in filtered_items:
                if isinstance(item_list, list):
                    flat_items.extend(item_list)
                else:
                    flat_items.append(item_list)
            
            # Create DataFrame
            df = pd.DataFrame(flat_items)
            
            # Clean up monetary values (remove $ and commas)
            if 'final_judgment_amount' in df.columns:
                df['final_judgment_amount'] = df['final_judgment_amount'].str.replace('$', '').str.replace(',', '').astype(float)
            if 'assessed_value' in df.columns:
                df['assessed_value'] = df['assessed_value'].str.replace('$', '').str.replace(',', '').astype(float)
            
            # rearrange columns so 'property_address' is first, 'assessed_value' is second and 'final_judgment_amount' is third
            df = df[['property_address', 'assessed_value', 'final_judgment_amount', 'auction_date', 'realtor_link']]
            
            # Generate timestamp for filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save to Excel
            excel_filename = f"filtered_{timestamp}.xlsx"
            df.to_excel(excel_filename, index=False)
            print(f"Filtered data saved to {excel_filename}")
        else:
            print("No items matched the filter criteria")