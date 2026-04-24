"""
Initialize the database with pre-fetched trail data.
Run this once to seed the database; scraper.py keeps it up to date afterward.
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'data', 'trails.db'))

DNR_BASE = 'https://www.dnr.state.mn.us/ohv/trail_detail.html?id='


def init_database():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trails (
            id INTEGER PRIMARY KEY,
            trail_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            counties TEXT,
            miles INTEGER,
            atv_miles INTEGER,
            ohv_miles INTEGER,
            ohm_miles INTEGER,
            morv_miles INTEGER,
            winter_miles INTEGER,
            status TEXT,
            status_notes TEXT,
            last_updated DATE,
            normal_season TEXT,
            dnr_url TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY,
            trail_id INTEGER,
            status TEXT,
            status_notes TEXT,
            recorded_at TIMESTAMP,
            FOREIGN KEY (trail_id) REFERENCES trails(trail_id)
        )
    ''')

    # Add columns added in later versions to existing databases
    for col, ctype in [('dnr_url', 'TEXT'), ('latitude', 'REAL'), ('longitude', 'REAL'), ('location_text', 'TEXT')]:
        try:
            cursor.execute(f'ALTER TABLE trails ADD COLUMN {col} {ctype}')
        except Exception:
            pass

    conn.commit()

    # Trail data seeded from DNR website — scraper.py will keep status current.
    # Columns: trail_id, name, counties, total_miles, atv, ohv, ohm, morv, winter,
    #          status, status_notes, last_updated, normal_season
    # Status values must be exactly: OPEN, Closed, Limited (scraper normalizes to these)
    trails = [
        (132, 'Agassiz Central Trail', 'Norman', 17, 17, 0, 0, 0, 0, 'Closed', '', '2026-04-11', 'April 1 to November 30'),
        (2, 'Agassiz Recreational Trail', 'Clay, Norman, Polk', 52, 52, 0, 0, 0, 0, 'OPEN', '', '2026-04-11', 'Year round'),
        (3, 'Alborn-Pengilly Railroad Trail', 'Itasca', 39, 39, 0, 0, 0, 0, 'Closed', 'MN Highway 73 to Alborn: Closed; Pengilly to MN Highway 73: Closed', '2026-04-11', 'May 15 to November 30'),
        (119, 'Alger Grade OHM Trail', 'Lake', 13, 0, 0, 13, 0, 0, 'Closed', '', '2026-04-11', 'Seasonal'),
        (98, 'Alvwood-Squaw Lake Trail', 'Itasca', 159, 159, 0, 0, 159, 0, 'Closed', '', '2026-04-11', 'Year round; closed 3/15 to 5/15'),
        (4, 'Appleton Area Recreational Park', 'Swift', 29, 29, 0, 0, 0, 0, 'OPEN', '', '2026-04-11', 'Winter riding available'),
        (94, 'Axtell Technical Riding Area', 'Aitkin', 1, 1, 0, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (106, 'Balsam Trail', 'Itasca', 6, 6, 6, 0, 0, 0, 'Closed', 'Check George Washington State Forest', '2026-04-11', ''),
        (57, 'Bemis Hill Trails', 'Roseau', 96, 96, 87, 0, 0, 0, 'OPEN', 'Check Beltrami Island State Forest', '2026-04-11', ''),
        (104, 'Bigfork and Balsam Connection', 'Itasca', 32, 32, 32, 0, 0, 0, 'Closed', 'Check George Washington State Forest', '2026-04-11', ''),
        (60, 'Blind Lake Connector and Loop', 'Aitkin', 3, 3, 3, 0, 0, 0, 'Closed', 'Check Hill River State Forest', '2026-04-11', ''),
        (5, 'Blue Ox Trail', 'Koochiching', 74, 74, 74, 0, 0, 0, 'Closed', 'Check Pine Island & Koochiching State Forests', '2026-04-11', ''),
        (120, 'C.J. Ramstad / North Shore State Trail', 'Lake', 7, 0, 0, 0, 0, 0, 'Closed', 'Check Finland State Forest', '2026-04-11', ''),
        (122, 'Consolidated Conservation Trails', 'Beltrami, Marshall', 93, 93, 93, 0, 0, 0, 'OPEN', 'Check Beltrami Island State Forest', '2026-04-11', ''),
        (74, 'Crow Wing Southern Loop Trail', 'Crow Wing', 60, 60, 0, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (123, 'Dailey Pits Trails', 'Mille Lacs', 8, 0, 8, 0, 0, 0, 'Closed', 'Closed for season. Check Rum River State Forest', '2026-04-11', ''),
        (114, 'David Dill - Taconite State Trail', 'St. Louis', 11, 11, 11, 0, 0, 0, 'Closed', 'Check Bear Island State Forest', '2026-04-11', ''),
        (134, 'Eastern Diversion Trail and Park', 'Roseau', 8, 8, 8, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (93, 'East Range Multi-Use Trail', 'St. Louis', 22, 22, 22, 0, 0, 0, 'OPEN', '', '2026-04-11', ''),
        (116, 'Emily - Blind Lake Trail', 'Crow Wing, Aitkin', 16, 16, 16, 0, 0, 0, 'Closed', 'Check Emily State Forest', '2026-04-11', ''),
        (70, 'Emily - Outing Trail', 'Cass', 56, 56, 56, 0, 0, 0, 'Closed', 'Check Land O Lakes State Forest', '2026-04-11', ''),
        (128, 'FireFrost Trail', 'Norman', 25, 0, 25, 0, 0, 0, 'OPEN', '', '2026-04-11', ''),
        (47, 'Fond du Lac State Forest Trails', 'Carlton', 37, 37, 37, 0, 27, 0, 'Closed', 'Check Fond du Lac State Forest', '2026-04-11', ''),
        (9, 'Forest Riders Trail', 'Hubbard', 12, 12, 12, 0, 0, 0, 'Closed', 'Check Smoky Hills & Two Inlets State Forests', '2026-04-11', ''),
        (10, 'Fort Ripley Trail and Ripley Connection', 'Crow Wing', 31, 31, 19, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (7, 'Fourtown-Grygla Trail', 'Beltrami', 17, 17, 12, 0, 0, 0, 'Closed', 'Check Beltrami Island State Forest', '2026-04-11', ''),
        (111, 'Foxy Loop', 'Mille Lacs', 3, 0, 3, 0, 0, 0, 'Closed', 'Closed for season', '2026-04-11', ''),
        (11, 'Gandy Dancer Trail', 'Pine', 30, 30, 30, 30, 0, 30, 'OPEN', 'Open to OHV 2000lbs and less. Check St. Croix & Nemadji State Forests', '2026-04-11', ''),
        (12, 'General C.C. Andrews State Forest Trails', 'Pine', 24, 24, 24, 0, 18, 0, 'OPEN', 'Check General C.C. Andrews State Forest', '2026-04-11', ''),
        (46, 'Genoa Trail', 'St. Louis', 33, 0, 0, 0, 3, 0, 'OPEN', '', '2026-04-11', ''),
        (69, 'Goodland Trail', 'Itasca', 19, 19, 19, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (95, 'Grant County Youth Trail', 'Grant', 3, 3, 3, 0, 0, 0, 'Closed', 'Closed for the season', '2026-04-11', ''),
        (126, 'Great Northern Connection Veterans Memorial Trail', 'Roseau', 26, 0, 26, 0, 0, 0, 'OPEN', 'Check Beltrami Island State Forest', '2026-04-11', ''),
        (131, 'Herb Brandstrom Trail', 'Itasca', 14, 0, 14, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (124, 'Hibbing to Alborn Trail', 'St. Louis', 18, 0, 18, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (61, 'Hill City Trail', 'Aitkin', 16, 0, 16, 0, 0, 0, 'Closed', 'Check Hill River State Forest', '2026-04-11', ''),
        (75, 'Hovland Woods Trail', 'Cook', 16, 0, 16, 0, 0, 0, 'Closed', 'Check Grand Portage State Forest', '2026-04-11', ''),
        (51, 'Huntersville Trail', 'Wadena', 73, 0, 73, 0, 0, 0, 'Closed', 'Due to Spring Breakup. Check Huntersville State Forest', '2026-04-11', ''),
        (112, 'Iron Range OHV State Recreation Area (West Unit)', 'St. Louis', 36, 36, 20, 0, 0, 0, 'OPEN', 'Leaf Lake loop, Bigfoot and Littlefoot closed for maintenance', '2026-04-11', ''),
        (13, 'Iron Range OHV State Recreation Area (East Unit)', 'St. Louis', 13, 0, 0, 0, 13, 0, 'OPEN', 'Leaf Lake loop, Bigfoot and Littlefoot closed for maintenance', '2026-04-11', ''),
        (76, 'Jackpot Trail', 'St. Louis', 30, 0, 30, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (113, 'Kelliher ATV Trail', 'Beltrami', 98, 0, 98, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (63, 'Lawler Loops', 'Aitkin', 16, 16, 16, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (127, 'Len Hardy Memorial Trail', 'Itasca', 9, 0, 9, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (59, 'Little Moose Trail', 'Itasca', 18, 18, 18, 0, 0, 0, 'Closed', 'Check George Washington State Forest', '2026-04-11', ''),
        (14, 'Martineau Recreational Trails', 'Hubbard', 97, 0, 97, 0, 0, 0, 'Closed', 'Check Paul Bunyan State Forest', '2026-04-11', ''),
        (109, 'Matthew Lourey State Trail OHV', 'Pine', 42, 0, 42, 0, 0, 0, 'Closed', 'Check St. Croix & Nemadji State Forests', '2026-04-11', ''),
        (71, 'Meeker County OHV Park', 'Meeker', 5, 0, 5, 0, 0, 0, 'Closed', 'Closed for the season', '2026-04-11', ''),
        (58, 'Mesabi Mountain Trail', 'St. Louis', 4, 0, 0, 4, 0, 0, 'Closed', '', '2026-04-11', ''),
        (121, 'Mille Lacs ORV Park', 'Mille Lacs', 5, 0, 0, 0, 0, 0, 'OPEN', '', '2026-04-11', ''),
        (72, 'Miller-Black Bear Trail', 'Crow Wing', 31, 0, 31, 0, 0, 0, 'Closed', 'Check Crow Wing State Forest', '2026-04-11', ''),
        (78, 'Miller Hills Trail', 'Crow Wing', 14, 0, 0, 14, 0, 0, 'Closed', '', '2026-04-11', ''),
        (97, 'Mississippi River Northwoods Trail', 'Crow Wing', 11, 0, 11, 11, 0, 0, 'Closed', '', '2026-04-11', ''),
        (65, 'Moose River Connector', 'Aitkin', 7, 0, 0, 7, 0, 0, 'Closed', '', '2026-04-11', ''),
        (15, 'Moose River Trail', 'Cass', 29, 0, 29, 0, 0, 0, 'Closed', 'Spring closure in effect. Check Land O Lakes State Forest', '2026-04-11', ''),
        (66, 'Moose Run Trail', 'Lake', 12, 0, 0, 0, 12, 0, 'Closed', 'Check Finland State Forest', '2026-04-11', ''),
        (16, 'Moose Walk Trail', 'Lake', 22, 0, 22, 0, 0, 0, 'Closed', 'Check Finland State Forest', '2026-04-11', ''),
        (37, 'Nemadji State Forest OHM Trails', 'Pine', 49, 0, 0, 49, 0, 0, 'Closed', 'Check Nemadji State Forest', '2026-04-11', ''),
        (33, 'Nemadji State Forest OHV Trails', 'Pine', 100, 100, 100, 100, 0, 103, 'Closed', 'Check Nemadji State Forest', '2026-04-11', ''),
        (133, 'Northwoods ATV Trails', 'Multiple', None, 0, 0, 0, 0, 0, 'Closed', 'See individual trails', '2026-04-11', ''),
        (108, 'Old Greenwood Trail', 'Cook', 30, 0, 30, 0, 0, 0, 'Closed', 'Check Pat Bayle State Forest', '2026-04-11', ''),
        (17, 'Pine Center Trails', 'Crow Wing', 23, 23, 23, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (118, 'Prospectors Trail', 'Lake, St. Louis', 167, 0, 163, 0, 0, 96, 'Closed', 'Check Bear Island & Finland State Forests', '2026-04-11', ''),
        (130, 'Quad Cities ATV Trail', 'St. Louis', 35, 0, 35, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (18, 'Rabey Line Trail', 'Aitkin', 19, 19, 19, 0, 0, 0, 'Closed', 'Check Hill River & Savanna State Forests', '2026-04-11', ''),
        (125, 'Rat Lake - Big Sandy Connector', 'Aitkin', 12, 0, 12, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (19, 'Red Dot Trail', 'Lake', 30, 0, 0, 0, 30, 0, 'Closed', 'Check Finland State Forest', '2026-04-11', ''),
        (20, 'Red Top Trail', 'Aitkin', 22, 0, 22, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (103, 'Rice Lake Pancore Loop', 'Cook', 13, 0, 0, 0, 13, 0, 'Closed', 'Check Pat Bayle State Forest', '2026-04-11', ''),
        (22, 'Round River Drive Trail', 'Hubbard', 113, 0, 113, 0, 0, 35, 'Closed', 'Check Paul Bunyan State Forest', '2026-04-11', ''),
        (99, 'Saginaw Grade/Lumberjack Multi-use Trail', 'Carlton', 10, 10, 10, 0, 0, 0, 'OPEN', '', '2026-04-11', ''),
        (50, 'Schoolcraft Trail', 'Hubbard', 29, 29, 29, 0, 0, 0, 'Closed', 'Check Paul Bunyan State Forest', '2026-04-11', ''),
        (100, 'Shady Oaks Native Prairie Adventure Trails', 'Lyon', 5, 0, 5, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (96, 'Smoky Hills ATV Trail', 'Becker', 20, 0, 20, 0, 0, 0, 'Closed', 'Check Smoky Hills State Forest', '2026-04-11', ''),
        (21, 'Snake Creek Trail', 'Wabasha', 13, 0, 13, 0, 0, 0, 'Closed', 'Trail closes at sunset October 31. Check Richard J. Dorer Memorial Hardwood Forest', '2026-04-11', ''),
        (45, 'Solana Loop', 'Aitkin', 15, 0, 15, 0, 0, 0, 'Closed', 'Check Solana State Forest', '2026-04-11', ''),
        (38, 'Soo Line North Trail: Aitkin County', 'Aitkin', 48, 48, 48, 0, 0, 0, 'Closed', 'Route change: Use Maddy Street in City of McGregor. Check Hill River State Forest', '2026-04-11', ''),
        (39, 'Soo Line North Trail: Carlton County', 'Carlton', 15, 15, 15, 0, 0, 0, 'OPEN', 'Check General C.C. Andrews State Forest', '2026-04-11', ''),
        (40, 'Soo Line North Trail: Cass County', 'Cass', 52, 52, 52, 0, 0, 0, 'OPEN', 'Unless Groomed For Snowmobiles. Check Bowstring State Forest', '2026-04-11', ''),
        (42, 'Soo Line South Trail: Aitkin County', 'Aitkin', 23, 23, 23, 0, 0, 0, 'OPEN', 'Check Solana State Forest', '2026-04-11', ''),
        (64, 'Soo Line South Trail: Carlton County', 'Carlton', 29, 0, 29, 0, 0, 0, 'OPEN', '', '2026-04-11', ''),
        (44, 'Soo Line South Trail: Mille Lacs County', 'Mille Lacs', 23, 23, 23, 0, 0, 0, 'OPEN', '', '2026-04-11', ''),
        (43, 'Soo Line South Trail: Morrison County', 'Morrison', 27, 0, 27, 0, 0, 0, 'OPEN', '', '2026-04-11', ''),
        (41, 'Soo Line South Trail: Pine County', 'Pine', 14, 14, 14, 0, 0, 0, 'OPEN', '', '2026-04-11', ''),
        (25, 'Soo Pits Trail', 'Carlton', 5, 0, 0, 0, 0, 0, 'OPEN', '', '2026-04-11', ''),
        (26, 'Southeast Minnesota Trail', 'Winona', 13, 0, 13, 0, 0, 0, 'Closed', 'Trail closes at sunset on 2nd Sunday in October', '2026-04-11', ''),
        (27, 'Spider Lake Trails', 'Cass', 29, 0, 26, 0, 0, 12, 'Closed', 'Spring closure in effect. Check Foot Hills State Forest', '2026-04-11', ''),
        (28, 'St. Croix State Forest Trails', 'Pine', 26, 26, 26, 7, 0, 0, 'Closed', 'Check St. Croix State Forest', '2026-04-11', ''),
        (29, 'Stony Spur II Trail', 'St. Louis', 30, 0, 30, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (110, 'Taconite State Trail - Big Aspen Connection', 'St. Louis', 18, 0, 0, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (30, 'Thistledew Trails', 'Itasca', 25, 0, 25, 0, 0, 0, 'Closed', 'Check George Washington State Forest', '2026-04-11', ''),
        (101, 'Timber Frear Loop', 'Cook', 20, 0, 0, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (105, 'Timber Trails', 'Beltrami', 114, 0, 114, 0, 0, 0, 'Closed', 'Check Blackduck & Buena Vista State Forests', '2026-04-11', ''),
        (34, 'Trout Valley Trail', 'Winona', 9, 0, 9, 0, 0, 0, 'Closed', 'Trail closes at sunset October 31 for the season.', '2026-04-11', ''),
        (115, 'Turkey Time Trail', 'St. Louis', 16, 16, 16, 10, 0, 0, 'OPEN', 'Check Fond du Lac State Forest', '2026-04-11', ''),
        (62, 'UPM Blandin Trail', 'Itasca', 21, 21, 21, 0, 0, 0, 'Closed', 'Check Hill River State Forest', '2026-04-11', ''),
        (117, 'Voyageur Country ATV', 'Lake', 36, 36, 36, 0, 0, 0, 'Closed', 'Check Kabetogama State Forest', '2026-04-11', ''),
        (68, 'Warroad/Roseau Trails', 'Roseau', 89, 89, 85, 0, 0, 82, 'Closed', 'ATVs not allowed on groomed snowmobile trails. Check Beltrami Island State Forest', '2026-04-11', ''),
        (77, 'Wild Country Trail', 'Lake', 30, 0, 30, 13, 0, 0, 'Closed', 'Check Finland State Forest', '2026-04-11', ''),
        (129, 'Wilderness Trail', 'Itasca', 60, 0, 60, 0, 0, 0, 'Closed', '', '2026-04-11', ''),
        (67, 'Wilton Trails Northwest', 'Beltrami', 37, 37, 37, 0, 0, 0, 'Closed', 'Check Mississippi Headwaters State Forest', '2026-04-11', ''),
    ]

    for t in trails:
        trail_id = t[0]
        dnr_url = f"{DNR_BASE}{trail_id}"
        cursor.execute('''
            INSERT OR REPLACE INTO trails
            (trail_id, name, counties, miles, atv_miles, ohv_miles, ohm_miles, morv_miles,
             winter_miles, status, status_notes, last_updated, normal_season, dnr_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', t + (dnr_url,))

    conn.commit()
    conn.close()
    print(f"Initialized database with {len(trails)} trails at {DATABASE}")


if __name__ == '__main__':
    init_database()
