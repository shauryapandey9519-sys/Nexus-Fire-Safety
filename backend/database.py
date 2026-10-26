"""
Nexus Fire Safety AI - Database Manager
Handles SQLite schema, incident logging, compliance audits, and initial seed data.
"""

import sqlite3
import os
import json
import time

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nexus_fire.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Incidents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_code TEXT UNIQUE,
        title TEXT NOT NULL,
        location TEXT NOT NULL,
        floor INTEGER NOT NULL,
        severity TEXT NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
        fire_class TEXT NOT NULL, -- 'Class A', 'Class B', 'Class C', 'Class K'
        suppression_medium TEXT NOT NULL,
        status TEXT NOT NULL, -- 'ACTIVE', 'CONTAINED', 'RESOLVED'
        detected_by TEXT NOT NULL, -- 'AI Vision Sentinel', 'IoT Thermal Array', 'Manual Pull Station'
        ai_summary TEXT,
        cad_dispatch TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    )
    """)

    # Compliance audit items table (NFPA / OSHA standards)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compliance_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        standard TEXT NOT NULL, -- 'NFPA 10', 'NFPA 72', 'NFPA 101', 'OSHA 1910.36'
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        requirement TEXT NOT NULL,
        status TEXT NOT NULL, -- 'COMPLIANT', 'WARNING', 'VIOLATION'
        last_inspected TEXT NOT NULL,
        inspector TEXT NOT NULL,
        remediation TEXT
    )
    """)

    # System activity logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        level TEXT NOT NULL, -- 'INFO', 'WARN', 'ALARM', 'ACTION'
        source TEXT NOT NULL,
        message TEXT NOT NULL
    )
    """)

    conn.commit()

    # Seed initial compliance checklist if empty
    cursor.execute("SELECT COUNT(*) FROM compliance_items")
    if cursor.fetchone()[0] == 0:
        seed_compliance_data(conn)

    # Seed initial incident history if empty
    cursor.execute("SELECT COUNT(*) FROM incidents")
    if cursor.fetchone()[0] == 0:
        seed_incident_data(conn)

    # Seed initial system logs if empty
    cursor.execute("SELECT COUNT(*) FROM system_logs")
    if cursor.fetchone()[0] == 0:
        seed_system_logs(conn)

    conn.close()

def seed_compliance_data(conn):
    items = [
        ("NFPA-10-A", "NFPA 10", "Fire Extinguishers", "Annual Hydrostatic Inspection", 
         "All dry-chemical and CO2 portable extinguishers must have valid inspection tags and full pressure gauge indicator.",
         "COMPLIANT", "2026-09-15", "Capt. M. Reynolds (Fire Marshal)", "Next annual inspection scheduled Sept 2027."),
        
        ("NFPA-10-B", "NFPA 10", "Fire Extinguishers", "Clear Extinguisher Clearance Zone", 
         "36 inches of unobstructed access must be maintained in front of all wall-mounted extinguishers at all times.",
         "WARNING", "2026-10-18", "Nexus Autonomous Vision Audit", "Server Room B spare rack temporarily obstructing CO2 extinguisher #4."),

        ("NFPA-72-A", "NFPA 72", "Alarm & Signaling", "Strobe & Horn Audibility Level", 
         "Emergency audible alarms must achieve at least 15 dB above ambient noise levels across all working areas.",
         "COMPLIANT", "2026-10-01", "Acoustic Sensor Mesh #9", "Measured at 92 dBA in open lab; compliant."),

        ("NFPA-72-B", "NFPA 72", "Alarm & Signaling", "Smoke Detector Sensitivity Drift", 
         "Optical smoke obscuration detectors must be tested within calibrated 0.2-3.8% obscuration/ft range.",
         "COMPLIANT", "2026-10-12", "Nexus IoT Diagnostics", "All 32 ceiling units calibrated and responsive."),

        ("NFPA-101-A", "NFPA 101", "Life Safety Code", "Emergency Exit Door Hardware & Latches", 
         "Panic hardware and unlatched push-bars must open with no more than 15 lbf in primary path of egress.",
         "COMPLIANT", "2026-09-28", "Nexus Facility Audit", "East Stairwell & South Exit panic bars inspected."),

        ("NFPA-101-B", "NFPA 101", "Life Safety Code", "Photoluminescent Egress Signage", 
         "Illuminated EXIT signs must remain visible for minimum 90 minutes during main power blackout.",
         "COMPLIANT", "2026-10-05", "Nexus Battery Backup Subsystem", "Lithium emergency pack test: 114 min endurance."),

        ("OSHA-1910-A", "OSHA 1910.36", "Means of Egress", "Corridor Minimum Egress Width", 
         "Corridors serving 50 or more occupants must retain minimum 44 inches continuous width without blockages.",
         "WARNING", "2026-10-24", "Vision AI Corridor Camera #3", "Pallet deliveries left in Corridor 2 West. Flagged for removal."),

        ("NFPA-13-A", "NFPA 13", "Sprinkler Systems", "Sprinkler Head Clearance (18-Inch Rule)", 
         "Unobstructed 18 inches clearance below sprinkler deflector heads across storage racking.",
         "COMPLIANT", "2026-10-20", "Nexus Spatial LiDAR Scan", "Racking top shelf meets 22.4 inch buffer.")
    ]

    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO compliance_items (code, standard, category, title, requirement, status, last_inspected, inspector, remediation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, items)
    conn.commit()

def seed_incident_data(conn):
    incidents = [
        ("NEX-2026-1021", "Lithium Battery Thermal Runaway (Bench Test)", "Chemistry Lab 4", 2, "HIGH", "Class B", 
         "Copper Powder / Class D Dry Powder", "RESOLVED", "AI Vision Sentinel",
         "Thermal imaging detected battery cell overheating past 160°C. Automated inert gas purge deployed in fume hood. No injuries reported.",
         "CAD DISPATCH TRANSMITTED: Box Alarm 441 - Apex Research Bldg 4. Fume hood containment active. Hazard neutralized.",
         "2026-10-21 14:15:22", "2026-10-21 14:38:10"),
        
        ("NEX-2026-0914", "HVAC Motor Overheat & Friction Smoke", "Roof Mechanical Room", 3, "MEDIUM", "Class C", 
         "CO2 Flooding System", "RESOLVED", "IoT Thermal Array",
         "Bearing friction caused heat spike (89°C) and light smoke in HVAC Air Handler #2. Nexus automated system cut motor power immediately.",
         "CAD DISPATCH TRANSMITTED: Non-structural alarm - Mechanical AHU-2 isolated. Facilities maintenance dispatched.",
         "2026-09-14 09:42:01", "2026-09-14 10:15:33")
    ]

    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO incidents (incident_code, title, location, floor, severity, fire_class, suppression_medium, status, detected_by, ai_summary, cad_dispatch, created_at, resolved_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, incidents)
    conn.commit()

def seed_system_logs(conn):
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    logs = [
        (now_str, "INFO", "Core Engine", "Nexus Fire Safety AI Engine initialized. 28 IoT sensor nodes online."),
        (now_str, "INFO", "AI Vision", "Sentinel Camera streams #1-#4 active at 30 FPS. Flame & smoke heuristics loaded."),
        (now_str, "INFO", "Pathfinding", "Dynamic Dijkstra graph mapped for Facility Building 4 (Level 1 & 2). 3 emergency exits verified clear."),
        (now_str, "INFO", "Safety Mesh", "Sprinkler pressure normal at 122 PSI. FM-200 Clean Agent banks armed.")
    ]
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO system_logs (timestamp, level, source, message) VALUES (?, ?, ?, ?)", logs)
    conn.commit()

def add_log(level, source, message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO system_logs (timestamp, level, source, message) VALUES (?, ?, ?, ?)",
                   (time.strftime("%Y-%m-%d %H:%M:%S"), level, source, message))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
