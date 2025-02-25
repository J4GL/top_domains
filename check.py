#!/usr/bin/env python3
# pip install requests tabulate colorama

import requests
import time
from urllib3.exceptions import InsecureRequestWarning
from requests.exceptions import RequestException
import sys
from tabulate import tabulate
import colorama
from colorama import Fore, Style

# Initialize colorama for colored terminal output
colorama.init()

# Suppress only the specific InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# List of sources to check
sources = {
    "Alexa": "https://web.archive.org/web/20230803120013/https://s3.amazonaws.com/alexa-static/top-1m.csv.zip",
    "Cisco Umbrella": "https://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip",
    "Majestic": "https://downloads.majestic.com/majestic_million.csv",
    "BuiltWith": "https://builtwith.com/dl/builtwith-top1m.zip",
    "Statvoo": "https://statvoo.com/dl/top-1million-sites.csv.zip",
    "DomCop": "https://www.domcop.com/files/top/top10milliondomains.csv.zip",
    "Tranco": "https://tranco-list.eu/top-1m.csv.zip",
    "Cloudflare": "https://radar.cloudflare.com/charts/LargerTopDomainsTable/attachment?id=1257&top=1000000"
}

def check_url(name, url):
    """Check if a URL is valid without downloading content using HEAD request"""
    print(f"Checking {name}: {url}")

    try:
        # Set a custom User-Agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
        }

        # Use a HEAD request first (minimal data transfer)
        response = requests.head(
            url,
            timeout=10,
            allow_redirects=True,
            headers=headers,
            verify=False  # Ignore SSL certificate errors
        )

        # If HEAD request fails with 405 Method Not Allowed, try GET request with stream=True
        # This still prevents downloading the full content
        if response.status_code == 405:
            response = requests.get(
                url,
                timeout=10,
                stream=True,  # Important: this prevents downloading the full content
                headers=headers,
                verify=False  # Ignore SSL certificate errors
            )
            # Close the connection immediately
            response.close()

        status_code = response.status_code
        is_valid = 200 <= status_code < 400

        return {
            "name": name,
            "url": url,
            "status_code": status_code,
            "is_valid": is_valid,
            "message": f"Valid source" if is_valid else f"Invalid source (Status: {status_code})"
        }

    except RequestException as e:
        error_message = str(e)
        return {
            "name": name,
            "url": url,
            "status_code": "Error",
            "is_valid": False,
            "message": f"Error: {error_message}"
        }

def main():
    results = {}

    # Check each URL
    for name, url in sources.items():
        result = check_url(name, url)
        results[name] = result

        # Print immediate result with color
        status_str = f"{Fore.GREEN}Valid ✓{Style.RESET_ALL}" if result["is_valid"] else f"{Fore.RED}Invalid ✗{Style.RESET_ALL}"
        print(f"Result: {status_str} ({result['status_code']})")

        # Wait a short time between requests to avoid overwhelming servers
        time.sleep(1)

    # Prepare data for tabulate
    table_data = []
    for name, result in results.items():
        status = f"{Fore.GREEN}Valid ✓{Style.RESET_ALL}" if result["is_valid"] else f"{Fore.RED}Invalid ✗{Style.RESET_ALL}"
        status_with_code = f"{status} ({result['status_code']})"
        table_data.append([name, status_with_code, result["url"]])

    # Print all results
    print("\n" + "=" * 80)
    print("SOURCE AVAILABILITY RESULTS")
    print("=" * 80)

    print(tabulate(
        table_data,
        headers=["Source", "Status", "URL"],
        tablefmt="grid"
    ))

    # Calculate statistics
    valid_count = sum(1 for result in results.values() if result["is_valid"])
    total_count = len(results)

    print(f"\nValid sources: {valid_count} / {total_count}")

    # Generate non-working sources summary
    non_working = [result for result in results.values() if not result["is_valid"]]

    if non_working:
        print("\n" + "=" * 80)
        print(f"{Fore.RED}NON-WORKING SOURCES SUMMARY{Style.RESET_ALL}")
        print("=" * 80)

        non_working_data = []
        for result in non_working:
            status_with_code = f"{Fore.RED}Invalid ✗{Style.RESET_ALL} ({result['status_code']})"
            non_working_data.append([result["name"], status_with_code, result["url"]])

        print(tabulate(
            non_working_data,
            headers=["Source", "Status", "URL"],
            tablefmt="grid"
        ))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(0)
