#!/usr/bin/env python3
import os
import sys
import json
import argparse

# --- Configuration ---
# Default paths - these can now be overridden by command-line arguments
DEFAULT_WORKRAVE_TXT_PATH = 'workrave_stats.txt'
DEFAULT_JSON_OUTPUT_PATH = 'workrave_stats.json'

# --- IMPORTANT: Try different encodings for input if UTF-8 doesn't work ---
# Common encodings: 'utf-8', 'latin-1', 'cp1252' (Windows ANSI)
input_encoding = 'utf-8'  # Start with UTF-8


# Function to parse individual lines
def parse_line(line):
    """Parses a single line from the WorkRave historystats file."""
    if line.startswith('D '):
        parts = line.split()
        # Expected format based on your snippets, e.g., "D 6 8 123 16 23 7 8 123 17 34"
        # Indices: 0(D) 1(start_day) 2(start_month) 3(start_year_code) 4(start_hour) 5(start_minute)
        #          6(end_day) 7(end_month) 8(end_year_code) 9(end_hour) 10(end_minute)
        if len(parts) >= 11:
            try:
                # Corrected Indexing and Year Calculation
                start_day = int(parts[1])
                start_month_raw = int(parts[2])  # WorkRave's month is 1-indexed
                start_year_code = int(parts[3])
                start_hour = int(parts[4])
                start_minute = int(parts[5])

                end_day = int(parts[6])
                end_month_raw = int(parts[7])  # WorkRave's month is 1-indexed
                end_year_code = int(parts[8])
                end_hour = int(parts[9])
                end_minute = int(parts[10])

                # Year calculation logic from process_workrave.py:
                start_year = 2000 + (start_year_code % 100)
                end_year = 2000 + (end_year_code % 100)

                # Convert month to 0-indexed for JSON/JavaScript Date objects
                start_month = start_month_raw - 1
                end_month = end_month_raw - 1

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
                return None
        else:
            print(f"Warning: Malformed D line (too few parts): {line.strip()}")
            return None
    elif line.startswith('B '):
        parts = line.split()
        # B <break_type> <val1> ... <val7> (8 values after B)
        if len(parts) >= 9:
            try:
                return {
                    "type": "break",
                    "break_type": int(parts[1]),
                    "values": [int(x) for x in parts[2:9]]  # Assuming 7 values after break_type
                }
            except (ValueError, IndexError) as e:
                print(f"Error parsing B line values: {line.strip()} - {e}")
                return None
        else:
            print(f"Warning: Malformed B line (too few parts): {line.strip()}")
            return None
    elif line.startswith('m '):
        parts = line.split()
        # m <workrave_id> <keystrokes> <mouse_movement_units> <mouse_clicks> <other1> <other2> (6 values after m)
        if len(parts) >= 7:
            try:
                return {
                    "type": "activity",
                    "workrave_id": int(parts[1]),
                    "keystrokes": int(parts[2]),
                    "mouse_movement_units": int(parts[3]),
                    "mouse_clicks": int(parts[4]),
                    "other_metrics": [int(x) for x in parts[5:7]]  # Assuming 2 other metrics
                }
            except (ValueError, IndexError) as e:
                print(f"Error parsing m line values: {line.strip()} - {e}")
                return None
        else:
            print(f"Warning: Malformed m line (too few parts): {line.strip()}")
            return None
    return None


# --- Main conversion script ---
def main(workrave_txt_path, json_output_path):
    """Main function to parse WorkRave data and convert it to JSON."""
    daily_stats = []
    current_daily_entry = None

    try:
        # Use an explicit check for encoding to provide better feedback
        content_lines = []
        try:
            with open(workrave_txt_path, 'r', encoding=input_encoding) as f:
                content_lines = f.readlines()
        except UnicodeDecodeError:
            print(f"Warning: Failed to decode '{workrave_txt_path}' with {input_encoding}. Trying 'latin-1'...")
            try:
                with open(workrave_txt_path, 'r', encoding='latin-1') as f:
                    content_lines = f.readlines()
            except UnicodeDecodeError:
                print(f"Error: Failed to decode '{workrave_txt_path}' with 'latin-1' too. Please check your file encoding.")
                return # Exit if encoding fails

        for line in content_lines:
            line = line.strip()
            if not line or line.startswith('WorkRaveStats'):  # Skip header or empty lines
                continue

            parsed_data = parse_line(line)

            if parsed_data:
                if parsed_data["type"] == "daily":
                    if current_daily_entry:  # Save the previous entry if it exists
                        daily_stats.append(current_daily_entry)
                    current_daily_entry = parsed_data
                    # Initialize activity_stats and break_stats for consistency
                    current_daily_entry.setdefault("break_stats", [])
                    current_daily_entry.setdefault("activity_stats", {
                        "workrave_id": 0, "keystrokes": 0, "mouse_movement_units": 0,
                        "mouse_clicks": 0, "other_metrics": [0, 0]
                    })
                elif current_daily_entry:  # Attach B or m lines to the current daily entry
                    if parsed_data["type"] == "break":
                        current_daily_entry["break_stats"].append({
                            "break_type": parsed_data["break_type"],
                            "values": parsed_data["values"]
                        })
                    elif parsed_data["type"] == "activity":
                        current_daily_entry["activity_stats"] = {
                            "workrave_id": parsed_data["workrave_id"],
                            "keystrokes": parsed_data["keystrokes"],
                            "mouse_movement_units": parsed_data["mouse_movement_units"],
                            "mouse_clicks": parsed_data["mouse_clicks"],
                            "other_metrics": parsed_data["other_metrics"]
                        }
                # else: pass # Skipping unparseable lines
            # If parsed_data is None (due to malformed line), it's skipped

        if current_daily_entry:  # Add the last entry after loop finishes
            daily_stats.append(current_daily_entry)

        json_string = json.dumps(daily_stats, indent=2, ensure_ascii=False)

        with open(json_output_path, 'w', encoding='utf-8') as json_file:
            json_file.write(json_string)

        print(f"Successfully converted '{workrave_txt_path}' to '{json_output_path}'")

    except FileNotFoundError:
        print(f"Error: The file '{workrave_txt_path}' was not found. Please ensure it's in the same directory as the script or provide the correct path.")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"An unexpected error occurred during conversion: {exc_type.__name__} - {e} at {fname} line {exc_tb.tb_lineno}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert WorkRave historystats text file to JSON format."
    )
    parser.add_argument(
        '-s', '--source',
        type=str,
        default=DEFAULT_WORKRAVE_TXT_PATH,
        help=f"Path to the source WorkRave historystats text file (default: {DEFAULT_WORKRAVE_TXT_PATH})"
    )
    parser.add_argument(
        '-d', '--destination',
        type=str,
        default=DEFAULT_JSON_OUTPUT_PATH,
        help=f"Path for the output JSON file (default: {DEFAULT_JSON_OUTPUT_PATH})"
    )
    args = parser.parse_args()

    main(args.source, args.destination)
