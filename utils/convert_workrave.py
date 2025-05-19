import os
import sys
import json

# --- Configuration ---
workrave_txt_path = 'samples/workrave_stats.txt' # Path to your WorkRave log file
json_output_path = 'samples/workrave_stats.json' # Desired output JSON file

# --- IMPORTANT: Try different encodings for input if UTF-8 doesn't work ---
# Common encodings: 'utf-8', 'latin-1', 'cp1252' (Windows ANSI)
# If you know the exact encoding of your original .txt file, use that.
# Otherwise, 'utf-8' is standard, but if it fails, try 'latin-1' or 'cp1252'.
input_encoding = 'utf-8' # Start with UTF-8
# input_encoding = 'latin-1' # Uncomment and try this if UTF-8 still gives ''
# input_encoding = 'cp1252' # Uncomment and try this if UTF-8 still gives ''

# Function to parse individual lines
def parse_line(line):
    if line.startswith('D '):
        parts = line.split()
        # Expected format based on snippet and user info:
        # D <day_s> <month_s> <year_code_s> <hour_s> <minute_s> <day_e> <month_e> <year_code_e> <hour_e> <minute_e>
        if len(parts) >= 11:
            try:
                # --- Corrected Year Calculation ---
                # Assuming year_code is 100 + (Year - 2000)
                # So, Year = 2000 + (year_code - 100)
                start_year_code = int(parts[4]) # Correct index based on snippet D 6 8 123 16 23...
                start_year = 2000 + (start_year_code - 100)

                end_year_code = int(parts[8]) # Correct index based on snippet
                end_year = 2000 + (end_year_code - 100)

                # Assuming month is 1-indexed in WorkRave stats (1=Jan, 8=Aug) based on snippet D 6 8...
                start_month = int(parts[2]) - 1 # Convert to 0-indexed for JSON/JS Date
                end_month = int(parts[6]) - 1   # Convert to 0-indexed for JSON/JS Date

                start_day = int(parts[1])
                end_day = int(parts[5])

                start_hour = int(parts[5]) # Correct index based on snippet
                start_minute = int(parts[9]) # Correct index based on snippet

                end_hour = int(parts[9]) # Correct index based on snippet
                end_minute = int(parts[10]) # Correct index based on snippet


                return {
                    "type": "daily",
                    "start_date": {"day": start_day, "month": start_month, "year": start_year},
                    "start_time": {"hour": start_hour, "minute": start_minute},
                    "end_date": {"day": end_day, "month": end_month, "year": end_year},
                    "end_time": {"hour": end_hour, "minute": end_minute},
                    "break_stats": [],
                    "activity_stats": {}
                }
            except (ValueError, IndexError) as e:
                print(f"Error parsing D line date/time or structure: {line.strip()} - {e}")
                return None # Return None for unparseable lines
    elif line.startswith('B '):
        parts = line.split()
        # B <break_type> <val1> ... <val7> (8 values after B)
        if len(parts) >= 9:
            try:
                return {
                    "type": "break",
                    "break_type": int(parts[1]),
                    "values": [int(x) for x in parts[2:9]] # Assuming 7 values after break_type
                }
            except (ValueError, IndexError) as e:
                print(f"Error parsing B line values: {line.strip()} - {e}")
                return None
    elif line.startswith('m '):
        parts = line.split()
        # m <workrave_id> <keystrokes> <mouse_movement_units> <mouse_clicks> <other1> <other2> <other3> (6 values after m)
        if len(parts) >= 7:
            try:
                return {
                    "type": "activity",
                    "workrave_id": int(parts[1]),
                    "keystrokes": int(parts[2]),
                    "mouse_movement_units": int(parts[3]),
                    "mouse_clicks": int(parts[4]),
                    "other_metrics": [int(x) for x in parts[5:7]] # Assuming 2 other metrics based on snippet
                }
            except (ValueError, IndexError) as e:
                print(f"Error parsing m line values: {line.strip()} - {e}")
                return None
    return None

# --- Main conversion script ---
daily_stats = []
current_daily_entry = None

try:
    # Open the input file with the specified encoding, handling errors
    # 'errors=ignore' can help skip bad chars if encoding is uncertain
    with open(workrave_txt_path, 'r', encoding=input_encoding, errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('WorkRaveStats'): # Skip header or empty lines
                continue

            parsed_data = parse_line(line)

            if parsed_data:
                if parsed_data["type"] == "daily":
                    if current_daily_entry: # Save the previous entry if it exists
                        daily_stats.append(current_daily_entry)
                    current_daily_entry = parsed_data
                elif current_daily_entry: # Attach B or m lines to the current daily entry
                    if parsed_data["type"] == "break":
                        current_daily_entry.setdefault("break_stats", []).append({
                            "break_type": parsed_data["break_type"],
                            "values": parsed_data["values"]
                        })
                    elif parsed_data["type"] == "activity":
                         # Overwrite activity_stats if multiple 'm' lines exist for a day (unlikely but safe)
                        current_daily_entry["activity_stats"] = {
                            "workrave_id": parsed_data["workrave_id"],
                            "keystrokes": parsed_data["keystrokes"],
                            "mouse_movement_units": parsed_data["mouse_movement_units"],
                            "mouse_clicks": parsed_data["mouse_clicks"],
                            "other_metrics": parsed_data["other_metrics"]
                        }
            else:
                # Log unparseable lines for debugging if needed
                # print(f"Skipping unparseable line: {line}")
                pass

    if current_daily_entry: # Add the last entry after loop finishes
        daily_stats.append(current_daily_entry)

    # Convert the list of dictionaries to a JSON string
    # ensure_ascii=False for proper Unicode characters
    json_string = json.dumps(daily_stats, indent=2, ensure_ascii=False)

    # Write the JSON string to the file, explicitly UTF-8, no BOM
    with open(json_output_path, 'w', encoding='utf-8') as json_file:
        json_file.write(json_string)

    print(f"Successfully converted '{workrave_txt_path}' to '{json_output_path}'")

except FileNotFoundError:
    print(f"Error: The file '{workrave_txt_path}' was not found. Please ensure it's in the same directory as the script.")
except Exception as e:
    # Use sys.exc_info() for more robust error reporting
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(f"An unexpected error occurred during conversion: {exc_type.__name__} - {e} at {fname} line {exc_tb.tb_lineno}")

