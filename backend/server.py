"""
Nexus Fire Safety AI - Main Full-Stack Server
Provides REST APIs, Server-Sent Events (SSE) real-time streaming, and static web serving.
Zero third-party dependencies: runs on Python 3.9+ standard library.
"""

import sys
import os
import json
import time
import mimetypes
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import init_db, get_connection, add_log
from backend.simulation import simulation
from backend.pathfinding import floorplan_engine
from backend.ai_engine import answer_safety_query, evaluate_drill_decision, generate_iap_report

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

# Ensure MIME types are properly registered
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/svg+xml", ".svg")

class NexusAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        # Enable CORS for local testing/hackathon judges
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Handle API routes
        if path.startswith("/api/"):
            self.handle_api_get(path, parse_qs(parsed.query))
            return

        # Serve index.html on root
        if path == "/" or path == "":
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        if path.startswith("/api/"):
            self.handle_api_post(path, payload)
            return

        self.send_error(404, "Endpoint not found")

    def send_json(self, data, status_code=200):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def handle_api_get(self, path, query_params):
        if path == "/api/status":
            state = simulation.get_state()
            self.send_json({"success": True, "data": state})

        elif path == "/api/evacuation":
            floorplan_data = floorplan_engine.get_floorplan_state()
            self.send_json({"success": True, "data": floorplan_data})

        elif path == "/api/incidents":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents ORDER BY id DESC")
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.send_json({"success": True, "data": rows})

        elif path == "/api/compliance":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compliance_items ORDER BY id ASC")
            rows = [dict(row) for row in cursor.fetchall()]
            
            # Compute compliance score
            total = len(rows)
            compliant = sum(1 for r in rows if r["status"] == "COMPLIANT")
            warnings = sum(1 for r in rows if r["status"] == "WARNING")
            violations = sum(1 for r in rows if r["status"] == "VIOLATION")
            score = int(((compliant * 1.0 + warnings * 0.5) / max(1, total)) * 100)
            
            conn.close()
            self.send_json({
                "success": True,
                "data": {
                    "score": score,
                    "grade": "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 65 else "FAIL",
                    "total": total,
                    "compliant": compliant,
                    "warnings": warnings,
                    "violations": violations,
                    "items": rows
                }
            })

        elif path == "/api/logs":
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 50")
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.send_json({"success": True, "data": rows})

        elif path == "/api/report/iap":
            state = simulation.get_state()
            report = generate_iap_report(state)
            self.send_json({"success": True, "data": report})

        elif path == "/api/stream":
            # Real-time Server-Sent Events (SSE) endpoint
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            try:
                while True:
                    state = simulation.get_state()
                    payload = f"data: {json.dumps(state)}\n\n"
                    self.wfile.write(payload.encode("utf-8"))
                    self.wfile.flush()
                    time.sleep(1.2)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_error(404, "API endpoint not found")

    def handle_api_post(self, path, payload):
        if path == "/api/simulation/start":
            scenario = payload.get("scenario", "electrical_server")
            state = simulation.set_scenario(scenario)
            self.send_json({"success": True, "scenario": scenario, "data": state})

        elif path == "/api/simulation/reset":
            state = simulation.set_scenario("normal")
            self.send_json({"success": True, "scenario": "normal", "data": state})

        elif path == "/api/simulation/hazard":
            room_id = payload.get("room_id", "server_b")
            temp = float(payload.get("temp", 75.0))
            smoke = float(payload.get("smoke", 35.0))
            flame = bool(payload.get("flame", True))
            state = simulation.set_room_hazard(room_id, temp, smoke, flame)
            self.send_json({"success": True, "room_id": room_id, "data": state})

        elif path == "/api/simulation/hazard/clear":
            room_id = payload.get("room_id", "server_b")
            state = simulation.clear_room_hazard(room_id)
            self.send_json({"success": True, "room_id": room_id, "data": state})

        elif path == "/api/ai/chat":
            user_query = payload.get("query", "")
            current_state = simulation.get_state()
            result = answer_safety_query(user_query, current_state)
            add_log("INFO", "AI Co-Pilot", f"Query processed: {user_query[:40]}...")
            self.send_json({"success": True, "data": result})

        elif path == "/api/drill/evaluate":
            drill_result = evaluate_drill_decision(payload)
            add_log("ACTION", "Drill Trainer", f"Participant completed drill: {drill_result['rank']} ({drill_result['score']}/100)")
            self.send_json({"success": True, "data": drill_result})

        elif path == "/api/incidents":
            title = payload.get("title", "Manual Emergency Incident")
            location = payload.get("location", "Building 4")
            floor = int(payload.get("floor", 1))
            severity = payload.get("severity", "HIGH")
            fire_class = payload.get("fire_class", "Class A")
            suppression = payload.get("suppression_medium", "Multi-Purpose Dry Chemical")
            detected_by = payload.get("detected_by", "Manual Dispatch")
            cad_dispatch = payload.get("cad_dispatch", "Manual 911 Alarm Triggered")

            code = f"NEX-MANUAL-{int(time.time())}"
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO incidents (incident_code, title, location, floor, severity, fire_class, suppression_medium, status, detected_by, ai_summary, cad_dispatch, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?)
            """, (code, title, location, floor, severity, fire_class, suppression, detected_by, 
                  f"Operator logged manual alarm: {title} at {location}.", cad_dispatch, time.strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()

            add_log("ALARM", "Operator", f"Manual Incident {code} created: {title}")
            self.send_json({"success": True, "incident_code": code})

        elif path == "/api/compliance/toggle":
            item_id = payload.get("id")
            new_status = payload.get("status", "COMPLIANT")
            if item_id:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE compliance_items SET status = ?, last_inspected = ? WHERE id = ?",
                               (new_status, time.strftime("%Y-%m-%d"), item_id))
                conn.commit()
                conn.close()
                add_log("ACTION", "Compliance", f"Item #{item_id} status updated to {new_status}")
                self.send_json({"success": True, "updated_id": item_id, "new_status": new_status})
            else:
                self.send_json({"success": False, "error": "Missing item id"}, status_code=400)
        else:
            self.send_error(404, "API endpoint not found")

def simulation_background_worker():
    """Runs continuous background ticks for physics & telemetry simulation."""
    while True:
        try:
            simulation.update_tick()
        except Exception as e:
            print("Simulation tick error:", e)
        time.sleep(1.0)

def run_server(port=8080):
    init_db()
    
    # Start background physics thread
    sim_thread = threading.Thread(target=simulation_background_worker, daemon=True)
    sim_thread.start()

    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, NexusAPIHandler)
    print(f"=====================================================")
    print(f" NEXUS FIRE SAFETY AI - FULL STACK SERVER ONLINE")
    print(f" Listening on http://localhost:{port}")
    print(f" Hackathon Demo & Command Console Ready")
    print(f"=====================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
