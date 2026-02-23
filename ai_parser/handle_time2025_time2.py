import datetime

def format_time_string_2(date_str, format_type):
    """
    Format time strings based on format_type.

    Args:
        date_str (str): Input string containing time parts separated by spaces or dots.
        format_type (int): 2 or 3, determines the output format.

    Returns:
        str: Formatted time string.
    """
    import re

    # Split the input string by spaces or dots to get time parts
    time_parts = re.split(r'[ \.]+', date_str.strip())

    formatted_times = []

    for part in time_parts:
        if ':' in part:
            # Already has colon, parse HH:MM or HH:MM:SS
            time_split = part.split(':')
            if len(time_split) >= 2:
                hour = time_split[0].zfill(2)
                minute = time_split[1].zfill(2)
                if format_type == 3:
                    formatted_times.append(f"{hour}:{minute}:00")
                elif format_type == 2:
                    formatted_times.append(f"{hour}:{minute}")
        elif '.' in part or part.isdigit():
            # Handle cases like "12.5" -> 12:30
            if '.' in part:
                hour, frac = part.split('.')
                hour = hour.zfill(2)
                if frac == '5':
                    minute = '30'
                else:
                    minute = '00'  # Default
            else:
                hour = part.zfill(2)
                minute = '00'
            if format_type == 3:
                formatted_times.append(f"{hour}:{minute}:00")
            elif format_type == 2:
                formatted_times.append(f"{hour}:{minute}")

    # Join based on format_type
    if format_type == 3:
        return '. '.join(formatted_times)
    elif format_type == 2:
        return ' '.join(formatted_times)
    else:
        return ' '.join(formatted_times)  # Default to format 2