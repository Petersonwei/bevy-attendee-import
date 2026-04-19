# Bevy Attendee Importer

Batch import attendees from CSV to GDG/Bevy events using browser automation.

## Why?

Bevy doesn't provide a bulk import feature for event registrations. This tool automates the manual process of adding attendees one by one through the dashboard UI.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

## First Run (Login)

The first time you run the script, you need to log in to Bevy:

```bash
python import_attendees.py --csv attendees.csv --event EVENT_ID --chapter CHAPTER_SLUG
```

A browser window will open. Log in with your Google account that has organizer access to the event. Your session will be saved in `~/.bevy-browser-profile` for future runs.

## Usage

```bash
python import_attendees.py --csv attendees.csv --event 119337 --chapter gdg-brisbane
```

### Options

| Option | Required | Description |
|--------|----------|-------------|
| `--csv` | Yes | Path to CSV file with attendees |
| `--event` | Yes | Event ID (from the Bevy dashboard URL) |
| `--chapter` | Yes | Chapter slug (e.g., `gdg-brisbane`) |
| `--delay` | No | Seconds between registrations (default: 2) |
| `--headless` | No | Run without browser window |

### Finding Event ID and Chapter Slug

From your event dashboard URL:
```
https://gdg.community.dev/dashboard/gdg-brisbane/events/119337/registrations
                                 ^^^^^^^^^^^^        ^^^^^^
                                 chapter slug        event ID
```

## Test CSV Loading

To verify your CSV is parsed correctly before importing:

```bash
python -c "
from import_attendees import load_attendees
attendees = load_attendees('your_file.csv')
print(f'Found {len(attendees)} attendees')
for a in attendees[:5]:  # Show first 5
    print(f'  - {a[\"first_name\"]} {a[\"last_name\"]} ({a[\"email\"]})')
"
```

## CSV Format

The script works with the standard Eventbrite attendee export format. It reads these columns:

| Column | Required |
|--------|----------|
| `Attendee first name` | Yes |
| `Attendee Surname` | Yes |
| `Attendee email` | Yes |

All other columns in the Eventbrite export are ignored.

See `example.csv` for the full Eventbrite export format.

## Notes

- The script uses a 2-second delay between registrations by default to avoid overwhelming the server
- Duplicate emails may be accepted by Bevy (it doesn't seem to validate uniqueness)
- Empty rows in the CSV are automatically skipped
- Failed imports are listed at the end for manual retry
