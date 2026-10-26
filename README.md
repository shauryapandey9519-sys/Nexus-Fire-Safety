# Nexus Fire Safety AI 🔥
### Autonomous Early Hazard Detection, Dynamic Evacuation Intelligence & Incident Command Coordination Platform

> **Hackathon Track**: Smart Cities / AI & Public Safety / Emergency Response & Defense / Edge IoT

---

## 🚀 Live Demo & Quick Start

The full-stack application runs with zero third-party dependencies using Python 3.9+ standard library and native modern web APIs.

### 1. Launch the Server
```bash
cd /Users/shaurya/.gemini/antigravity/scratch/nexus-fire-safety-ai
python3 backend/server.py 8080
```

### 2. Open in Browser
Visit **[http://localhost:8080](http://localhost:8080)** in Chrome, Edge, Safari, or Firefox.

---

## 🎯 The Problem

In high-density commercial complexes, data centers, chemical research laboratories, and hospitals:
1. **Traditional alarms are blunt instruments**: Loud bells blare indiscriminately without spatial awareness. Occupants don't know *where* the fire is or which corridors are blocked by smoke.
2. **First-responder information blindspot**: Firefighters arrive on-scene minutes later without knowing the fire classification (e.g. applying water to an electrical or grease fire causes explosions).
3. **Delayed evacuation routing**: Panic leads people into smoke-filled stairwells or dead ends.
4. **Manual Life Safety Compliance Audits**: Inspections are done on paper clipboards every 6 months, leaving hazardous violations (blocked exits, expired extinguishers) undetected until catastrophe strikes.

---

## 💡 The Nexus Solution

**Nexus Fire Safety AI** is an end-to-end intelligence platform that integrates edge computer vision, IoT environmental telemetry, graph-theoretic pathfinding, and automated emergency dispatch:

```
                          ┌───────────────────────────┐
                          │   Edge IoT Sensor Mesh    │
                          │ (Temp, Smoke, CO, VOC)    │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
┌───────────────────────────┐     ┌───────────┐     ┌───────────────────────────┐
│  Vision AI Sentinel Feed  │────▶│ AI Engine │◀────│  NFPA 10/72/101 Standards │
│ (Flame, Smoke Kinematics) │     │ (Defcon & │     │      Compliance Ledger    │
└───────────────────────────┘     │ Reasoner) │     └───────────────────────────┘
                                        │
                                        ▼
                 ┌──────────────────────────────────────────────┐
                 │         Dynamic Orchestration Hub            │
                 ├──────────────────────┬───────────────────────┤
                 │ Dynamic Dijkstra     │ Automated 911 CAD     │
                 │ Evacuation Routing   │ Dispatch Transmission │
                 └──────────────────────┴───────────────────────┘
```

---

## 🌟 Key Features

### 1. 🧠 Vision AI Sentinel (CCTV & Live WebCam)
- Continuous video analytics detecting flame corona flicker patterns, rising smoke kinematics, and optical flow vectors.
- **Interactive Live WebCam Mode**: Judges can click **"Connect Live WebCam"** to test client-side computer vision live with a candle, lighter, or flame photo! Real-time bounding boxes render with confidence ratings.

### 2. 🗺️ Dynamic Dijkstra Evacuation Engine (Interactive 2D Canvas)
- Architectural blueprint of Apex BioTech Research Facility (Building 4).
- Graph-theoretic pathfinding algorithm recalculates shortest escape routes from every room in **< 100 milliseconds**.
- If a fire breaks out in Server Room B, the system marks the West junction as hazardous (blocked red markers) and reroutes occupants to East and South loading dock exits.
- Animated flowing green arrows and simulated moving occupant beacons show live evacuation flow.

### 3. 🚨 AI Incident Commander & Automated 911 CAD Dispatch
- Auto-generates standard NFPA 901 Computer-Aided Dispatch (CAD) payloads formatted for emergency dispatchers:
  - Exact GPS coordinates & nearest hydrant distance (PSI rating)
  - Construction type (Type II-A Protected Non-combustible)
  - Fire Classification (Class A, B, C, or K)
  - Mandated Suppression Agent (FM-200 Clean Agent, Potassium Acetate Wet Chemical, High Expansion Foam)
  - Prohibited agents warning (e.g. *DO NOT USE WATER ON SERVER B*)
  - One-click copy to clipboard for dispatchers.

### 4. 🔊 Authentic NFPA 72 Audio Synthesizer & Voice Dispatch
- Built using the native HTML5 Web Audio API: synthesizes the exact NFPA 72 Temporal-3 piercing alarm horn (3 pulses of 500ms on, 500ms off, followed by 1500ms silence).
- Built-in speech synthesis announces spoken emergency instructions: *"Warning. Fire hazard detected in Server Room B. Evacuate via East Stairwell."*

### 5. 📈 IoT Environmental Sensor Mesh & Real-Time Trend Charts
- 7 monitored zones: Server Room B, Chemistry Lab 4, Cafeteria & Commercial Kitchen, Open Workspace, Executive Briefing Suite, Mechanical Substation, and Central Reception.
- Monitors Temperature (°C), Smoke Obscuration (%/ft), Carbon Monoxide (ppm), VOC (ppb), and Sprinkler Manifold Pressure (PSI).
- High-performance canvas chart plotting live multi-variable historical trends.

### 6. 📋 Life Safety & NFPA Code Compliance Audit
- Interactive digital inspection ledger tracking compliance with NFPA 10, NFPA 72, NFPA 101, and OSHA 1910.36.
- Live grading score (0-100%, Grade A-F).
- Interactive status dropdowns save updates directly to the SQLite backend.

### 7. ✨ Nexus AI Fire Safety Co-Pilot (Interactive Emergency Assistant)
- Persistent floating AI drawer with contextual awareness of current building alarms, sensor values, and NFPA standards.
- Instant pre-set queries: Lithium battery fires in Server B, safe egress corridor audits, kitchen saponification, emergency PA broadcasts, and flashover physics.
- Includes speech synthesis voice narration for first responders and operators.

### 8. 🎯 Interactive Fire Commander Drill Trainer
- Gamified hackathon decision trainer allowing judges to test their incident command instincts under pressure.
- Evaluates suppression agent selection, HVAC damper isolation, and egress routing, calculating a score (0-100) and certifying the commander rank.

### 9. 📄 Official NFPA 901 Incident Action Plan (IAP) & PDF Print Generator
- Generates official ICS Form 202/204 Incident Action Plans formatted with operational period, command staff, tactical life safety objectives, hazard telemetry ledgers, and logistics data.
- 1-click printable with dedicated print media formatting.

### 10. 📢 Facility Public Address (EVACS) Broadcast Console
- Two-tone emergency chime synthesis via HTML5 Web Audio API followed by speech-synthesized public address announcements with customizable presets (Evacuation, Shelter-in-Place, All-Clear).

---

## 🕹️ Interactive Hackathon Demo Scenarios

Use the top scenario bar or What-If Sandbox to trigger live emergency simulations:
1. **🟢 Normal Operations**: All zones green, ambient sensors nominal, Defcon 4.
2. **⚡ Server Electrical Fire (Class C)**: Temperature spikes in Server Room B, Clean Agent FM-200 discharge primed, West corridor smoke migration, evacuation routes rerouted to East Stairwell and South Loading Dock.
3. **🍳 Kitchen Grease Flashover (Class K)**: Cafeteria grease vat flashover, Wet Chemical suppression activated, natural gas solenoid closed, West courtyard evacuation active.
4. **🧪 Chemical Solvent Ignition (Class B)**: Flammable vapor ignition in Chemistry Lab 4, HazMat task force dispatched, negative-pressure scrubber active.
5. **⚡ What-If Sandbox**: Click any room on the floorplan to inject custom thermal spikes (84°C) or dense smoke (45%) to watch the Dijkstra pathfinder recalculate escape vectors live!

---

## 🛠️ Technical Stack & Architecture

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.9+ `http.server.ThreadingHTTPServer`, `sqlite3`, `threading`, `json` |
| **Streaming** | Server-Sent Events (SSE) `/api/stream` pushing live state at 1.2s intervals |
| **Database** | SQLite3 (`data/nexus_fire.db`) storing incidents, audits, and system logs |
| **Pathfinding** | Dynamic Dijkstra Graph Algorithm (`backend/pathfinding.py`) |
| **AI Engine** | Threat Evaluator, Tactical Suppression Reasoner, Safety Co-Pilot (`backend/ai_engine.py`) |
| **Frontend UI** | Modern Vanilla JavaScript (ES6+), Glassmorphic CSS, Custom Canvas 2D |
| **Audio Engine** | Native Web Audio API (NFPA 72 Temporal-3 pulse & PA Chimes) + Web Speech API |
| **Vision AI** | Client-Side Canvas Computer Vision + Backend Optical Plume Heuristics |

---

## 📡 REST API Reference

- `GET /api/status` — Full system telemetry, active threats, sensor readings, and evacuation routes.
- `GET /api/stream` — Real-time Server-Sent Events (SSE) telemetry pipeline.
- `GET /api/evacuation` — Floorplan room geometry, waypoints, and dynamic Dijkstra route vectors.
- `POST /api/simulation/start` — Triggers specific emergency scenario (`{"scenario": "electrical_server"}`).
- `POST /api/simulation/reset` — Resets simulation to normal baseline.
- `POST /api/simulation/hazard` — Injects custom hazard into any room (`{"room_id": "...", "temp": 84, "smoke": 45}`).
- `POST /api/simulation/hazard/clear` — Clears custom room hazard.
- `POST /api/ai/chat` — Queries Nexus AI Co-Pilot with real-time building context (`{"query": "..."}`).
- `POST /api/drill/evaluate` — Evaluates interactive drill decision choices (`{"scenario": "...", "suppression": "...", "hvac": "...", "egress": "..."}`).
- `GET /api/report/iap` — Generates NFPA 901 Incident Action Plan (ICS Form 202/204).
- `GET /api/incidents` — Incident history list.
- `POST /api/incidents` — Log new emergency incident.
- `GET /api/compliance` — NFPA / OSHA audit checklist and overall compliance grade.
- `POST /api/compliance/toggle` — Update compliance status of an audit item.
