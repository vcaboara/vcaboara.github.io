import json
import re

def convert_workrave_stats_to_json(input_filepath="workrave_stats.txt"):
    """
    Converts WorkRave statistics from a text file to a JSON array.

    Assumes the following format for lines:
    - D: Daily statistics (e.g., D <day> <month> <year> <h_start> <m_start> <day> <month> <year> <h_end> <m_end>)
         Parses into 'daily_stats' with start and end timestamps.
    - B: Break statistics (e.g., B <break_type> <val1> <val2> ...)
         Parses into 'break_stats' associated with the most recent 'D' entry.
    - m: Mouse/keyboard activity (e.g., m <val1> <val2> ...)
         Parses into 'activity_stats' associated with the most recent 'D' entry.
    """
    
    stats_data = []
    current_day_entry = None

    try:
        with open(input_filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if not parts:
                    continue

                if parts[0] == "WorkRaveStats":
                    # This line indicates the version, can be stored as a global metadata or ignored per daily stats
                    # For simplicity, we'll just acknowledge it and not add to each daily entry.
                    # Or, you could add it as a top-level key in the final JSON.
                    # print(f"WorkRaveStats version: {parts[1]}")
                    pass
                elif parts[0] == "D":
                    # Start of a new day's statistics
                    if current_day_entry:
                        stats_data.append(current_day_entry)
                    
                    # Assuming D format: D <day_s> <month_s> <year_s> <hour_s> <minute_s> <day_e> <month_e> <year_e> <hour_e> <minute_e>
                    # Adjust parsing based on actual snippet: D <value1> <value2> ...
                    # The snippets suggest: D <day> <month> <rest_interval> <k_start> <m_start> <day> <month> <rest_interval> <k_end> <m_end>
                    # Given the sample, it seems to be day, month, some identifier, hour, minute, repeated for start and end times.
                    # Let's use generic names if the exact meaning isn't clear from the 'historystats' doc.
                    # Based on the given snippet, it looks like:
                    # D <day_start> <month_start> <year_start> <hour_start> <minute_start> <day_end> <month_end> <year_end> <hour_end> <minute_end>
                    # Example: D 6 8 123 16 23 7 8 123 17 34
                    # This would mean:
                    # D <day> <month> <something> <k_s> <m_s> <day> <month> <something> <k_e> <m_e>
                    # From the github link it implies:
                    # D (day_of_month) (month_of_year) (year - 1900) (keystrokes_start) (mouse_start) (day_of_month) (month_of_year) (year - 1900) (keystrokes_end) (mouse_end)
                    try:
                        current_day_entry = {
                            "type": "daily",
                            "start_date": {
                                "day": int(parts[1]),
                                "month": int(parts[2]),
                                "year": int(parts[3]) + 1900 # Assuming year is offset from 1900
                            },
                            "start_time": {
                                "hour": int(parts[4]),
                                "minute": int(parts[5])
                            },
                            "end_date": {
                                "day": int(parts[6]),
                                "month": int(parts[7]),
                                "year": int(parts[8]) + 1900
                            },
                            "end_time": {
                                "hour": int(parts[9]),
                                "minute": int(parts[10])
                            },
                            "break_stats": [],
                            "activity_stats": {}
                        }
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Could not parse D line {line_num}: '{line}' - {e}")
                        current_day_entry = None # Reset to avoid attaching subsequent B/m lines incorrectly
                        continue

                elif parts[0] == "B" and current_day_entry:
                    # Break statistics
                    # B <break_type> <total_scheduled> <total_taken> <early_count> <late_count> <skipped_count> <start_total> <finish_total> <duration_total>
                    try:
                        break_type = int(parts[1]) # 0, 1, 2 based on snippet
                        current_day_entry["break_stats"].append({
                            "break_type": break_type,
                            "values": [int(p) for p in parts[2:]]
                        })
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Could not parse B line {line_num}: '{line}' - {e}")

                elif parts[0] == "m" and current_day_entry:
                    # Mouse/keyboard activity statistics
                    # m <total_k_count> <total_m_count> <total_m_dist> <total_clicks> <left_clicks> <right_clicks>
                    try:
                        current_day_entry["activity_stats"] = {
                            "total_keystrokes": int(parts[2]),
                            "total_mouse_clicks": int(parts[5]), # Assuming parts[5] is total clicks from a common format
                            "total_mouse_distance": int(parts[3]), # Assuming parts[3] is mouse distance
                            "misc_values": [int(p) for p in parts[1:]] # Store all as misc for now
                        }
                        # Refined parsing based on common WorkRave m line format:
                        # m <total_keystrokes> <total_mouse_movement> <total_mouse_clicks> <total_time_on_keyboard> <total_time_on_mouse> <break_compliance_score>
                        # Adjusting based on snippet: m 6 15917 3331728 1905193 885 1960 16878
                        # The snippet `m 6 15917 3331728 1905193 885 1960 16878`
                        # This appears to be `m <some_id> <keystrokes> <mouse_movement_units> <mouse_clicks> <unknown_1> <unknown_2> <unknown_3>`
                        # Let's adapt the parsing to be more generic for now.
                        current_day_entry["activity_stats"] = {
                            "workrave_id": int(parts[1]),
                            "keystrokes": int(parts[2]),
                            "mouse_movement_units": int(parts[3]),
                            "mouse_clicks": int(parts[4]),
                            "other_metrics": [int(p) for p in parts[5:]]
                        }

                    except (ValueError, IndexError) as e:
                        print(f"Warning: Could not parse m line {line_num}: '{line}' - {e}")
                else:
                    # Optionally handle other lines or log unparsed lines
                    # print(f"Skipping unparsed line {line_num}: '{line}'")
                    pass

        # Append the last day's entry if it exists
        if current_day_entry:
            stats_data.append(current_day_entry)

        return json.dumps(stats_data, indent=2)

    except FileNotFoundError:
        return f"Error: The file '{input_filepath}' was not found."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    json_output = convert_workrave_stats_to_json()
    print(json_output)
