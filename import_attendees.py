#!/usr/bin/env python3
"""
Bevy Attendee Importer
Batch import attendees from CSV to GDG/Bevy events via browser automation.

Usage:
    python import_attendees.py --csv attendees.csv --event EVENT_ID --chapter CHAPTER_SLUG
"""

import argparse
import csv
import os
import time
from playwright.sync_api import sync_playwright


# Default settings
DEFAULT_DELAY = 2  # seconds between registrations
USER_DATA_DIR = os.path.expanduser("~/.bevy-browser-profile")


def load_attendees(csv_path):
    """Load attendees from CSV file.

    Expected columns: 'Attendee first name', 'Attendee Surname', 'Attendee email'
    (Standard Bevy/Eventbrite export format)
    """
    attendees = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            first_name = row.get('Attendee first name', '').strip()
            last_name = row.get('Attendee Surname', '').strip()
            email = row.get('Attendee email', '').strip()

            # Skip empty rows
            if not first_name or not email:
                continue

            attendees.append({
                'first_name': first_name,
                'last_name': last_name,
                'email': email
            })
    return attendees


def add_attendee(page, modal, attendee, index, total):
    """Add a single attendee via the modal form. Returns True on success."""
    print(f"[{index + 1}/{total}] {attendee['first_name']} {attendee['last_name']} ({attendee['email']})")

    try:
        # Fill form fields
        modal.locator('input[name="first_name"]').fill(attendee['first_name'])
        modal.locator('input[name="last_name"]').fill(attendee['last_name'])
        modal.locator('input[name="email"]').fill(attendee['email'])

        # Check Terms and Conditions checkbox (force=True bypasses SVG overlay)
        terms_checkbox = modal.locator('input#signup_consent')
        if not terms_checkbox.is_checked():
            terms_checkbox.click(force=True)

        # Click Save
        modal.locator('button:has-text("Save")').first.click()

        # Wait for modal to close
        time.sleep(1)

        if not modal.is_visible():
            print(f"   ✓ Success")
            return True
        else:
            print(f"   ✗ Failed (modal still open)")
            # Close modal for next attempt
            close_btn = modal.locator('button[aria-label="Close"], button:has-text("Cancel")').first
            if close_btn.is_visible():
                close_btn.click()
                time.sleep(0.5)
            return False

    except Exception as e:
        print(f"   ✗ Error: {e}")
        try:
            page.locator('button[aria-label="Close"]').first.click()
        except:
            pass
        return False


def main():
    parser = argparse.ArgumentParser(description='Import attendees to Bevy event')
    parser.add_argument('--csv', required=True, help='Path to CSV file with attendees')
    parser.add_argument('--event', required=True, help='Event ID')
    parser.add_argument('--chapter', required=True, help='Chapter slug (e.g., gdg-brisbane)')
    parser.add_argument('--delay', type=int, default=DEFAULT_DELAY, help=f'Delay between registrations in seconds (default: {DEFAULT_DELAY})')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no browser window)')
    args = parser.parse_args()

    # Build dashboard URL
    dashboard_url = f"https://gdg.community.dev/dashboard/{args.chapter}/events/{args.event}/registrations"

    # Load attendees
    attendees = load_attendees(args.csv)
    if not attendees:
        print("No attendees found in CSV file.")
        return

    print("=" * 60)
    print("Bevy Attendee Importer")
    print("=" * 60)
    print(f"Event:     {args.event}")
    print(f"Chapter:   {args.chapter}")
    print(f"Attendees: {len(attendees)}")
    print(f"Delay:     {args.delay}s between each")
    print("=" * 60)

    with sync_playwright() as p:
        print("\nLaunching browser...")

        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=args.headless,
            args=['--disable-blink-features=AutomationControlled'],
            ignore_default_args=['--enable-automation'],
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto(dashboard_url)

        # Wait for page to be ready
        print("Waiting for page to load...")
        try:
            page.get_by_role("button", name="Add registration").wait_for(timeout=30000)
        except:
            print("\nERROR: Could not find 'Add registration' button.")
            print("Make sure you're logged in. Run once with browser visible to log in.")
            input("Press ENTER to close...")
            context.close()
            return

        print("Page ready, starting import...\n")

        # Process attendees
        success = 0
        failed = []

        for i, attendee in enumerate(attendees):
            # Click Add registration button
            page.get_by_role("button", name="Add registration").click()

            # Wait for modal
            page.wait_for_selector('[class*="Modal-styles__modal"], [role="dialog"]', timeout=5000)
            time.sleep(0.3)

            modal = page.locator('[class*="Modal-styles__modal"], [role="dialog"]').first

            if add_attendee(page, modal, attendee, i, len(attendees)):
                success += 1
            else:
                failed.append(attendee)

            # Delay before next (except last)
            if i < len(attendees) - 1:
                time.sleep(args.delay)

        # Summary
        print("\n" + "=" * 60)
        print("IMPORT COMPLETE")
        print("=" * 60)
        print(f"Success: {success}")
        print(f"Failed:  {len(failed)}")

        if failed:
            print("\nFailed attendees:")
            for att in failed:
                print(f"  - {att['first_name']} {att['last_name']} ({att['email']})")

        context.close()


if __name__ == '__main__':
    main()
