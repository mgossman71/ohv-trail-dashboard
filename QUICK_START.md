# OHV Trail Dashboard - Quick Start Script

Run these commands to initialize the database:

```bash
cd /root/.openclaw/workspace/ohv-trail-dashboard

# Run the init script inside the container
docker compose exec ohv-trail-dashboard python init_container_db.py

# Verify the data is there
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) FROM trails;"
```

Then refresh your browser at http://oc1:8000/