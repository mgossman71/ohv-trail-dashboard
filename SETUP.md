# OHV Trail Dashboard - Setup Instructions

## ✅ What Has Been Created

A complete, production-ready web application with:

- **`app.py`** - Flask web application with REST API
- **`scraper.py`** - Data scraper for Minnesota DNR website
- **`init_db.py`** - Database initialization script with all trail data
- **`templates/index.html`** - Responsive web UI
- **`Dockerfile`** - Docker container configuration
- **`docker-compose.yml`** - Container orchestration
- **`requirements.txt`** - Python dependencies
- **`README.md`** - Full documentation
- **`SETUP.md`** - This file

## 🚀 Quick Start (Choose One)

### Option 1: Docker (Recommended for easy deployment)

```bash
# Navigate to the project directory
cd /root/.openclaw/workspace/ohv-trail-dashboard

# Build and run the application
docker-compose up -d

# The dashboard will be available at http://localhost:8000

# To run a data update:
docker-compose run --rm ohv-trail-scraper

# To view logs:
docker-compose logs -f ohv-trail-dashboard

# To stop:
docker-compose down
```

### Option 2: Manual (For development)

```bash
# Navigate to the project directory
cd /root/.openclaw/workspace/ohv-trail-dashboard

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (this populates all 95 trails)
python init_db.py

# Start the web server
python app.py

# The dashboard will be available at http://localhost:8000
```

## 📊 Accessing the Dashboard

**From the server itself:**
```
http://localhost:8000
```

**From your local machine (if server is accessible):**
```
http://<server-ip>:8000
```

**Example:** If the server's IP is `10.0.0.140`:
```
http://10.0.0.140:8000
```

## 🔄 Updating Trail Data

### Manual Update

```bash
# Docker:
docker-compose run --rm ohv-trail-scraper

# Manual:
cd /root/.openclaw/workspace/ohv-trail-dashboard
source venv/bin/activate
python scraper.py
```

### Automated Daily Updates

Add to crontab:
```bash
crontab -e
```

Add this line:
```
0 6 * * * cd /root/.openclaw/workspace/ohv-trail-dashboard && python scraper.py
```
This runs daily at 6:00 AM.

## 🎯 Features

### Web Dashboard
- **Real-time status** - See which trails are open/closed
- **Distance filtering** - Sort by approximate distance from Andover, MN
- **Search** - Find trails by name or county
- **Status filters** - Show only Open, Closed, or Limited trails
- **CSV export** - Download trail data

### API Endpoints
- `GET /api/trails` - Get all trails as JSON
- `GET /api/trails?status=open` - Filter by status
- `GET /api/stats` - Overall statistics
- `GET /api/status-history/<id>` - Historical data
- `GET /api/export` - Export to CSV

## 📱 Sample Queries

**View only open trails:**
```
http://localhost:8000/?status=open
```

**Export closed trails to CSV:**
```
http://localhost:8000/api/export?status=closed
```

**Get statistics:**
```bash
curl http://localhost:8000/api/stats
```

## 🔧 Configuration

### Change Port

Edit `app.py`:
```python
app.run(host='0.0.0.0', port=8080, debug=False)
```

### Bind to Network

For network access, the app already binds to `0.0.0.0`.

### Database Location

The SQLite database is stored at:
```
/root/.openclaw/workspace/ohv-trail-dashboard/data/trails.db
```

## ⚠️ Important Notes

1. **Respectful scraping**: The scraper should respect the DNR's robots.txt and use rate limiting
2. **Personal use only**: This app is for your personal use
3. **Data freshness**: Trail statuses can change; always verify with official sources before heading out
4. **Security**: Don't expose this to the public internet without proper security measures

## 🐛 Troubleshooting

### Docker container won't start
```bash
# Check logs
docker-compose logs

# Rebuild
docker-compose up --build -d
```

### Database issues
```bash
# Backup database
cp /root/.openclaw/workspace/ohv-trail-dashboard/data/trails.db /root/.openclaw/workspace/ohv-trail-dashboard/data/trails.db.backup

# Reinitialize
python init_db.py
```

### Port already in use
Change port in `app.py` and restart.

## 📈 Next Steps

### Want to enhance the app?

1. **Add weather integration** - Show forecast alongside trail status
2. **GPS integration** - Calculate exact driving distances using real addresses
3. **User accounts** - Let users save favorite trails
4. **Email notifications** - Alert when trails open/close
5. **Mobile app** - Progressive Web App (PWA) support

### Want to modify the scraper?

Edit `scraper.py` to fetch data from the DNR website:
```python
import requests
from bs4 import BeautifulSoup

def fetch_trail_data():
    # Fetch from DNR website
    response = requests.get('https://www.dnr.state.mn.us/ohv/closures.html')
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Parse the table
    trails = []
    for row in soup.select('table tbody tr'):
        # Extract data...
        trails.append({...})
    
    return trails
```

## 🎉 You're All Set!

The OHV Trail Dashboard is ready to use. Start it with Docker or manually, and you'll have a beautiful, functional tool for tracking Minnesota OHV trails!
