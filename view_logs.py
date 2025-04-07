#!/usr/bin/env python3
"""
Log viewer utility for the Databricks Gateway API wrapper.
This script provides a formatted view of the API request logs.
"""

import sys
import re
import json
from datetime import datetime
import argparse
import os

# ANSI color codes for terminal output
COLORS = {
    'RESET': '\033[0m',
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'MAGENTA': '\033[95m',
    'CYAN': '\033[96m',
    'WHITE': '\033[97m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m'
}

def colorize(text, color):
    """Add color to text for terminal output"""
    return f"{COLORS.get(color, '')}{text}{COLORS['RESET']}"

def format_json(json_str):
    """Format JSON string for better readability"""
    try:
        parsed = json.loads(json_str)
        return json.dumps(parsed, indent=2)
    except:
        return json_str

def parse_log_line(line):
    """Parse a log line into timestamp, level, and message"""
    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.*)', line)
    if match:
        timestamp, level, message = match.groups()
        return {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
    return None

def group_request_logs(log_lines):
    """Group log lines by request"""
    requests = []
    current_request = None
    
    for line_data in log_lines:
        if line_data is None:
            continue
            
        message = line_data['message']
        
        # Start of a new request
        if message.startswith('INCOMING REQUEST'):
            if current_request:
                requests.append(current_request)
            current_request = {
                'timestamp': line_data['timestamp'],
                'type': message.split(' - ')[1],
                'details': []
            }
        
        # Add details to current request
        if current_request:
            current_request['details'].append(line_data)
    
    # Add the last request
    if current_request:
        requests.append(current_request)
        
    return requests

def display_request(request, verbose=False):
    """Display a formatted request"""
    print(colorize(f"\n{'='*80}", 'BOLD'))
    print(colorize(f"REQUEST: {request['type']} at {request['timestamp']}", 'BOLD'))
    print(colorize(f"{'='*80}", 'BOLD'))
    
    # Track what we've seen to organize output
    has_request_headers = False
    has_request_body = False
    has_outgoing_request = False
    has_response = False
    has_error = False
    
    for detail in request['details']:
        message = detail['message']
        level = detail['level']
        
        # Request Headers
        if message.startswith('Request Headers:'):
            has_request_headers = True
            if verbose:
                print(colorize("\nREQUEST HEADERS:", 'BLUE'))
                headers_str = message.replace('Request Headers: ', '')
                try:
                    headers = eval(headers_str)
                    for key, value in headers.items():
                        print(f"  {colorize(key, 'CYAN')}: {value}")
                except:
                    print(f"  {headers_str}")
        
        # Request Body
        elif message.startswith('Request Body:'):
            has_request_body = True
            print(colorize("\nREQUEST BODY:", 'BLUE'))
            body_str = message.replace('Request Body: ', '')
            print(f"  {format_json(body_str)}")
        
        # Outgoing Request
        elif message.startswith('OUTGOING REQUEST'):
            has_outgoing_request = True
            print(colorize("\nOUTGOING REQUEST:", 'MAGENTA'))
            print(f"  {message.split(' - ')[1]}")
        
        # Outgoing Headers
        elif message.startswith('Outgoing Headers:'):
            if verbose:
                print(colorize("\nOUTGOING HEADERS:", 'MAGENTA'))
                print(f"  {message.replace('Outgoing Headers: ', '')}")
        
        # Outgoing Body
        elif message.startswith('Outgoing Body:'):
            print(colorize("\nOUTGOING BODY:", 'MAGENTA'))
            body_str = message.replace('Outgoing Body: ', '')
            print(f"  {format_json(body_str)}")
        
        # Response
        elif message.startswith('RESPONSE from Databricks'):
            has_response = True
            print(colorize("\nRESPONSE:", 'GREEN'))
            print(f"  {message.split(' - ')[1]}")
        
        # Response Body
        elif message.startswith('Response Body:'):
            print(colorize("\nRESPONSE BODY:", 'GREEN'))
            body_str = message.replace('Response Body: ', '')
            print(f"  {format_json(body_str)}")
        
        # Error
        elif level == 'ERROR' or message.startswith('ERROR'):
            has_error = True
            print(colorize("\nERROR:", 'RED'))
            print(f"  {message}")
        
        # Error Response Body
        elif message.startswith('Error Response Body:'):
            print(colorize("\nERROR RESPONSE BODY:", 'RED'))
            body_str = message.replace('Error Response Body: ', '')
            print(f"  {format_json(body_str)}")
    
    # Summary
    print(colorize("\nSUMMARY:", 'YELLOW'))
    print(f"  Request Type: {colorize(request['type'], 'BOLD')}")
    print(f"  Timestamp: {request['timestamp']}")
    if has_request_body:
        print(f"  Request Body: {colorize('Yes', 'GREEN')}")
    if has_outgoing_request:
        print(f"  Forwarded to Databricks: {colorize('Yes', 'GREEN')}")
    if has_response:
        print(f"  Received Response: {colorize('Yes', 'GREEN')}")
    if has_error:
        print(f"  Errors: {colorize('Yes', 'RED')}")
    else:
        print(f"  Errors: {colorize('No', 'GREEN')}")

def main():
    parser = argparse.ArgumentParser(description='View and analyze API request logs')
    parser.add_argument('-f', '--file', default='api_requests.log', help='Log file to analyze')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose output including headers')
    parser.add_argument('-n', '--num', type=int, help='Number of most recent requests to show')
    parser.add_argument('-e', '--errors', action='store_true', help='Show only requests with errors')
    args = parser.parse_args()
    
    # Check if log file exists
    if not os.path.exists(args.file):
        print(colorize(f"Error: Log file '{args.file}' not found.", 'RED'))
        return 1
    
    # Read log file
    with open(args.file, 'r') as f:
        lines = f.readlines()
    
    # Parse log lines
    log_lines = [parse_log_line(line) for line in lines]
    
    # Group by request
    requests = group_request_logs(log_lines)
    
    # Filter requests if needed
    if args.errors:
        requests = [r for r in requests if any(d['level'] == 'ERROR' for d in r['details'])]
    
    # Limit number of requests if specified
    if args.num and args.num > 0:
        requests = requests[-args.num:]
    
    # Display requests
    if not requests:
        print(colorize("No matching requests found in the log file.", 'YELLOW'))
        return 0
    
    print(colorize(f"Found {len(requests)} requests in log file", 'BOLD'))
    
    for request in requests:
        display_request(request, args.verbose)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())