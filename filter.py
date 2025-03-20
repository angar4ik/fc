# scan all json files in fc directory and subdirectories
# filter items by given parameters (e.g. assessed value > judgment value, assessed value in bewtwwen 80k and 120k)
# create a new json file with filtered items
import os
import json
from lib.filter_data import FilterData

# path to directory with json files
path = "./fc"
# list of filtered items
filtered_items = []

# walk through directory and subdirectories
for root, dirs, files in os.walk(path):
    # loop through files
    for file in files:
        # only process json files
        if file.endswith('.json'):
            try:
                file_path = os.path.join(root, file)
                # open file
                with open(file_path) as f:
                    # load json
                    data = json.load(f)
                    # check if data has auction_items
                    if isinstance(data, dict) and 'auction_items' in data:
                         filtered_items.append(FilterData().filer(data, min = 130000, max = 180000))

            except PermissionError:
                print(f"Permission denied: {file_path}")
            except json.JSONDecodeError:
                print(f"Invalid JSON in file: {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")

print(len(filtered_items))

FilterData().save_to_excel(filtered_items)
