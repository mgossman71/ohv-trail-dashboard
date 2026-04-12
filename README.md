# OHV Trail Dashboard

A personal web application for browsing Minnesota OHV trail statuses, sorted by distance from Andover, MN (55304).

## Features

- **Real-time trail status** - See which trails are open/closed
- **Distance sorting** - Trails sorted by approximate distance from Andover, MN
- **Search & filtering** - Filter by status (Open, Closed, Limited) or search by name
- **Historical tracking** - Status changes are tracked over time
- **CSV export** - Export trail data for offline use
- **Responsive design** - Works on desktop and mobile

## Quick Start

### Using Docker

```bash
# Build and run
cd ohv-trail-dashboard
docker-compose up -d

# View the dashboard
open http://localhost:8000

# Run a manual scrape
docker-compose run --rm ohv-trail-scraper python scraper.py

# View logs
docker-compose logs -f ohv-trail-dashboard
```

### Manual Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Start the web server
python app.py
```

## Configuration

### Access

By default, the app runs on `http://localhost:8000`. To access it from other devices:

- **Local network only**: Change `app.run(host='0.0.0.0', ...)` to bind to your network IP
- **Exposed to internet**: Set up reverse proxy (nginx) with SSL (NOT recommended without proper security)

### Update Frequency

The scraper should run daily. Set up a cron job:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6 AM
0 6 * * * cd /path/to/ohv-trail-dashboard && python scraper.py
```

Or use the Docker container with scheduled runs.

## Data Source

Data is scraped from the [Minnesota DNR OHV Trails page](https://www.dnr.state.mn.us/ohv/). 

**Note**: The DNR's robots.txt restricts automated scraping of individual trail detail pages. This app uses respectful rate limiting and is for personal use only.

## Architecture

- **Backend**: Python Flask REST API
- **Database**: SQLite (trail data + status history)
- **Frontend**: Simple HTML/CSS/JavaScript with sorting and filtering
- **Deployment**: Docker containers for easy deployment

## Database Schema

```sql
-- Main trails table
trails (
    id, trail_id, name, counties, miles,
    atv_miles, ohv_miles, ohm_miles, morv_miles, winter_miles,
    status, status_notes, last_updated, normal_season
)

-- Status history for tracking changes
status_history (
    id, trail_id, status, status_notes, recorded_at
)
```

## API Endpoints

- `GET /` - Main dashboard page
- `GET /api/trails` - JSON endpoint for all trails
- `GET /api/trails?status=open` - Filter by status
- `GET /api/status-history/<trail_id>` - Historical status data
- `GET /api/stats` - Overall statistics (counts)
- `GET /api/export?status=all` - Export to CSV

## Development

### Adding New Features

1. Update `app.py` for new API endpoints or routes
2. Update `templates/index.html` for UI changes
3. Update `scraper.py` to fetch new data fields

### Testing

```bash
# Run tests
pytest tests/

# Test scraper manually
python scraper.py

# Test API
curl http://localhost:8000/api/stats
```

## License

This project is for personal use only. The data belongs to Minnesota DNR.

## Disclaimer

Always verify trail status with official DNR resources before heading out. This app is a convenience tool and may not always have the most up-to-date information.
