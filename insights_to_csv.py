import json
import csv
import os

# --- Configuration ---

# Map of FIPS codes to county names
FIPS_COUNTY_MAP = {
    "24001": "Allegany", "24003": "Anne Arundel", "24005": "Baltimore",
    "24007": "Baltimore City", "24009": "Calvert", "24011": "Caroline",
    "24013": "Carroll", "24015": "Cecil", "24017": "Charles",
    "24019": "Dorchester", "24021": "Frederick", "24023": "Garrett",
    "24025": "Harford", "24027": "Howard", "24029": "Kent",
    "24031": "Montgomery", "24033": "Prince George's", "24035": "Queen Anne's",
    "24037": "St. Mary's", "24039": "Somerset", "24041": "Talbot",
    "24043": "Washington", "24045": "Wicomico", "24047": "Worcester",
    "24510": "Baltimore City"
}

INPUT_FILE = 'html/aiInsights.json'
OUTPUT_FILE = 'ai_insights_output.csv'

# --- Main Script ---

def convert_json_to_csv():
    """
    Loads AI insights from a JSON file, processes it, and saves it as a CSV.
    """
    print(f"Starting conversion for '{INPUT_FILE}'...")

    # --- 1. Load Input JSON ---
    try:
        # Read the JSON data
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{INPUT_FILE}'. Check file format.")
        return
    except Exception as e:
        print(f"An error occurred loading the file: {e}")
        return

    processed_rows = []
    
    # --- 2. Process Data ---
    print("Processing JSON data...")
    for key, qa_list in data.items():
        # Split the key (e.g., "Commodity Cover Crop_24001")
        try:
            # Use rsplit to split on the *last* underscore, just in case
            # the indicator name ever contains an underscore.
            indicator, county_fips = key.rsplit('_', 1)
        except ValueError:
            print(f"Warning: Skipping malformed key: '{key}'")
            continue
            
        # Look up the county name
        county_name = FIPS_COUNTY_MAP.get(county_fips, "Unknown")
        
        # Ensure the value is a list before iterating
        if not isinstance(qa_list, list):
            print(f"Warning: Skipping key '{key}', expected a list but got {type(qa_list)}")
            continue

        # Create a row for each question/answer pair
        for item in qa_list:
            question = item.get('question', '')
            answer = item.get('answer', '')
            
            processed_rows.append([
                county_fips,
                county_name,
                indicator,
                question,
                answer
            ])

    # --- 3. Write Output CSV ---
    if not processed_rows:
        print("No valid data was processed. Output file will not be created.")
        return

    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write the header
            writer.writerow(['county_fips', 'county_name', 'indicator', 'question', 'answer'])
            
            # Write all the processed rows
            writer.writerows(processed_rows)
            
        print(f"\nSuccess! Conversion complete.")
        print(f"Processed {len(processed_rows)} insights.")
        print(f"Output saved to '{OUTPUT_FILE}'")

    except IOError as e:
        print(f"Error writing to output file '{OUTPUT_FILE}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during writing: {e}")


# --- Run the script ---
if __name__ == "__main__":
    convert_json_to_csv()
