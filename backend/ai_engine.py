"""
Nexus Fire Safety AI - AI Incident Commander & Vision Sentinel Engine
Provides real-time fire threat evaluation, automated 911 CAD dispatch generation,
fire classification, tactical suppression agent recommendations, and computer vision analytics.
"""

import math
import time

def evaluate_threat(telemetry):
    """
    telemetry: dict of sensor readings across rooms
    Returns risk_score (0-100), severity, recommendations, and tactical breakdown.
    """
    max_temp = telemetry.get("max_temp", 22.0)
    max_smoke = telemetry.get("max_smoke", 0.1)
    max_co = telemetry.get("max_co", 3.0)
    flame_detected = telemetry.get("flame_detected", False)
    room_id = telemetry.get("active_room", "normal")

    # Base risk score calculation
    temp_factor = min(40, max(0, (max_temp - 25) * 0.7))
    smoke_factor = min(35, max_smoke * 0.8)
    co_factor = min(25, (max_co / 100.0) * 25)
    flame_bonus = 30 if flame_detected else 0

    risk_score = min(100, int(temp_factor + smoke_factor + co_factor + flame_bonus))

    if risk_score >= 70 or flame_detected or max_temp > 65:
        severity = "CRITICAL"
        defcon = 1
    elif risk_score >= 45 or max_temp > 45 or max_smoke > 20:
        severity = "HIGH"
        defcon = 2
    elif risk_score >= 20 or max_temp > 32:
        severity = "ELEVATED"
        defcon = 3
    else:
        severity = "NORMAL"
        defcon = 4

    # Fire classification and tactical intelligence
    tactical = generate_tactical_plan(room_id, severity, max_temp, max_smoke)

    return {
        "risk_score": risk_score,
        "severity": severity,
        "defcon_level": defcon,
        "thermal_index_c": round(max_temp, 1),
        "smoke_obscuration_pct": round(max_smoke, 1),
        "co_density_ppm": round(max_co, 1),
        "flame_detected": flame_detected,
        "flashover_risk_pct": min(98, int((max_temp / 120.0) * 100)) if max_temp > 40 else 2,
        "tactical": tactical
    }

def generate_tactical_plan(room_id, severity, temp, smoke):
    """
    Generates NFPA compliant suppression recommendations and automated dispatch payloads.
    """
    plans = {
        "server_b": {
            "fire_class": "Class C (Energized Electrical)",
            "primary_agent": "FM-200 Clean Agent / Novec 1230 Total Flooding",
            "avoid_agent": "Standard Water Sprinklers (High risk of short-circuit explosion & server destruction)",
            "ventilation": "Seal Dampers. Initiate HVAC recirc shut-off to starve oxygen without fanning sparks.",
            "hazards": "High voltage racks (480V 3-phase), Lithium UPS battery backup strings in Rack 4.",
            "search_priority": "Server B IT Technician Bay, Server Corridor West",
            "dispatch_cad": {
                "box_code": "BOX 441-C (ELECTRICAL HIGH-RISE)",
                "facility": "Apex BioTech Research Facility, Building 4 - Level 1",
                "lat_lon": "37.7749° N, 122.4194° W",
                "nearest_hydrant": "Hydrant #12 (45m North Entrance, 140 PSI)",
                "recommended_units": ["Engine 12", "Truck 4 (Aerial)", "HazMat Unit 1", "Battalion Chief 2"],
                "tactical_radio_note": "ATTN ENGINE 12: Electrical Class C confirmed by AI Vision Sentinel in Server Room B. Do not apply solid water stream. Requesting Clean Agent suppression verification. Primary egress: East Stairwell clear."
            }
        },
        "cafeteria": {
            "fire_class": "Class K (Commercial Cooking Oils & Grease)",
            "primary_agent": "Wet Chemical (Potassium Acetate / Carbonate Saponification)",
            "avoid_agent": "Water streams (Will cause violent catastrophic grease flash boilover)",
            "ventilation": "Trigger Kitchen Hood Exhaust Damper Isolation; close gas supply solenoid valve.",
            "hazards": "Deep fat fryer vats (45 gallons vegetable oil), natural gas manifold lines.",
            "search_priority": "Kitchen Prep Room, Dishwashing Scullery, Dining Area",
            "dispatch_cad": {
                "box_code": "BOX 442-K (COMMERCIAL KITCHEN FIRE)",
                "facility": "Apex BioTech Research Facility - Cafeteria Wing",
                "lat_lon": "37.7751° N, 122.4190° W",
                "nearest_hydrant": "Hydrant #8 (30m South Loading Dock, 125 PSI)",
                "recommended_units": ["Engine 7", "Rescue 3", "Medic 9", "Truck 2"],
                "tactical_radio_note": "ATTN BATTALION CHIEF: Kitchen hood suppression activated. Automated solenoid closed natural gas mainline. Evacuating 18 occupants through West Courtyard."
            }
        },
        "chem_lab": {
            "fire_class": "Class B / D (Volatile Organic Solvents & Pyrophoric Reagents)",
            "primary_agent": "Class D Dry Powder / High-Expansion Foam Purge",
            "avoid_agent": "Pressurized Water (Vapor explosion risk with solvent pool fires)",
            "ventilation": "Immediate Emergency Fume Hood Negative-Pressure Scrubber active.",
            "hazards": "Acetone, Hexane drum storage, Lithium Hydride bench canisters.",
            "search_priority": "Solvent Storage Cabinet A, Fume Hood 4, Lab Office 402",
            "dispatch_cad": {
                "box_code": "BOX 443-HAZ (CHEMICAL LAB FLAMEOVER)",
                "facility": "Apex BioTech Research Facility - Chemistry Lab 4",
                "lat_lon": "37.7753° N, 122.4188° W",
                "nearest_hydrant": "Hydrant #15 (20m East Entrance, 150 PSI)",
                "recommended_units": ["HazMat Task Force 1", "Engine 14 (Foam Tender)", "Decon Unit 2", "Medic 4"],
                "tactical_radio_note": "ATTN HAZMAT 1: Chemical fire Level 3. Toxic VOC threshold exceeded. Level B PPE mandatory. Water prohibited on bench 2."
            }
        }
    }

    if room_id in plans and severity != "NORMAL":
        return plans[room_id]

    # Baseline nominal plan
    return {
        "fire_class": "Class A (Ordinary Combustibles) - Baseline",
        "primary_agent": "Automatic Quick-Response Wet Pipe Sprinkler (NFPA 13)",
        "avoid_agent": "None (Atmospheric conditions normal)",
        "ventilation": "Normal HVAC filtration (ASHRAE 62.1 cycle). Air turnover nominal.",
        "hazards": "None detected. All 28 environmental nodes within safety threshold.",
        "search_priority": "Routine surveillance across all zones",
        "dispatch_cad": {
            "box_code": "STANDBY - NO ACTIVE ALARM",
            "facility": "Apex BioTech Research Facility - Building 4",
            "lat_lon": "37.7749° N, 122.4194° W",
            "nearest_hydrant": "Hydrant #12 (45m North Entrance)",
            "recommended_units": ["Local Security Unit 1"],
            "tactical_radio_note": "All zones green. Automated detection mesh nominal."
        }
    }

def analyze_camera_feed(camera_id, scenario_state):
    """
    Simulates Vision Sentinel computer vision pipeline for real-time bounding box detection,
    confidence scoring, and flame/smoke kinematics.
    """
    timestamp = time.time()
    
    # Check if this camera corresponds to the active hazard scenario
    is_fire_cam = False
    if scenario_state == "electrical_server" and camera_id == "cam_server":
        is_fire_cam = True
    elif scenario_state == "kitchen_flashover" and camera_id == "cam_cafe":
        is_fire_cam = True
    elif scenario_state == "chemical_lab" and camera_id == "cam_lab":
        is_fire_cam = True

    if is_fire_cam:
        return {
            "camera_id": camera_id,
            "status": "FIRE_DETECTED",
            "flame_detected": True,
            "smoke_detected": True,
            "flame_confidence": 0.94 + 0.05 * math.sin(timestamp * 4),
            "smoke_density_pct": 68.4 + 5.0 * math.cos(timestamp * 2),
            "bounding_boxes": [
                {
                    "label": "CLASS C FLAME CORONA",
                    "confidence": 0.96,
                    "x_pct": 38,
                    "y_pct": 42,
                    "w_pct": 24,
                    "h_pct": 32,
                    "color": "#ef4444"
                },
                {
                    "label": "SMOKE PLUME EXPANSION",
                    "confidence": 0.89,
                    "x_pct": 32,
                    "y_pct": 18,
                    "w_pct": 36,
                    "h_pct": 28,
                    "color": "#f97316"
                }
            ],
            "optical_flow_vector": {"dx": 1.4, "dy": -3.8}, # rising plume
            "thermal_hotspot_c": 82.5 + 4.0 * math.sin(timestamp)
        }
    else:
        return {
            "camera_id": camera_id,
            "status": "NORMAL_SURVEILLANCE",
            "flame_detected": False,
            "smoke_detected": False,
            "flame_confidence": 0.02,
            "smoke_density_pct": 0.4,
            "bounding_boxes": [],
            "optical_flow_vector": {"dx": 0.0, "dy": 0.0},
            "thermal_hotspot_c": 22.4
        }


def answer_safety_query(user_query, current_state=None):
    """
    Intelligent Nexus Fire Safety AI Co-Pilot Query Engine.
    Combines NFPA standards, tactical firefighting protocols, chemical MSDS hazard knowledge,
    and real-time live sensor state to answer user/judge questions authoritatively.
    """
    query = (user_query or "").lower().strip()
    
    # Extract live context if available
    scenario = current_state.get("scenario", "normal") if current_state else "normal"
    threat = current_state.get("threat", {}) if current_state else {}
    severity = threat.get("severity", "NORMAL")
    sensors = current_state.get("sensors", {}) if current_state else {}
    
    # Active live hazard note
    live_context_alert = ""
    if severity in ["HIGH", "CRITICAL"]:
        live_room = "Server Room B" if scenario == "electrical_server" else "Cafeteria Kitchen" if scenario == "kitchen_flashover" else "Chemistry Lab 4" if scenario == "chemical_lab" else "Monitored Zone"
        live_temp = threat.get("thermal_index_c", 75.0)
        live_context_alert = f"> ⚠️ **LIVE EMERGENCY IN PROGRESS**: Defcon 1 active in **{live_room}** (Peak: {live_temp}°C). Dynamic Dijkstra evacuation rerouting is in effect.\n\n"

    # 1. Lithium-ion / Battery / Server / Data Center
    if any(k in query for k in ["lithium", "battery", "rack 4", "server", "data center", "ups", "electrical", "class c"]):
        return {
            "reply": (
                f"{live_context_alert}### ⚡ Tactical Protocol: Class C Electrical & Lithium-Ion Thermal Runaway (NFPA 855 & 2001)\n\n"
                "**1. Immediate Suppression Medium:**\n"
                "- **Primary Agent:** **FM-200 (HFC-227ea)** or **Novec 1230 (FK-5-1-12)** total flooding clean agent within 10 seconds.\n"
                "- ⛔ **CRITICAL WARNING:** **NEVER apply solid water streams** or plain ABC dry chemical directly to energized 480V server cabinets or lithium cells. Solid water conducts electricity to responders; dry powder creates corrosive hydrogen fluoride/ammonium phosphate crust that permanently destroys circuitry.\n\n"
                "**2. HVAC & Damper Strategy:**\n"
                "- Automatically trigger **HVAC recirculation dampers closed** to starve oxygen supply and avoid propagating dense hydrochloric acid / fluorinated gas fumes into adjacent corridors.\n"
                "- Engage dedicated negative-pressure battery exhaust scrubbers once containment seals verify.\n\n"
                "**3. First-Responder Tactical Directive:**\n"
                "- Disconnect Remote Power Off (EPO) shunt trip switch located at Main Electrical Distribution Board Room 102.\n"
                "- Utilize thermal imaging cameras (TIC) to detect cell-to-cell thermal propagation in battery rack modular strings.\n"
                "- Mandate **Exit B (East Fire Stairwell)** for occupant egress; West Server Corridor is isolated as a smoke barrier."
            ),
            "suggested_actions": ["Isolate Server B Dampers", "Check Battery Rack 4 Thermals", "Notify Engine 12 CAD"],
            "code_references": ["NFPA 855 (Energy Storage Systems)", "NFPA 2001 (Clean Agent Systems)", "NFPA 70E (Electrical Safety)"],
            "spoken_summary": "Class C electrical protocol requires clean agent suppression. Do not use water. East stairwell is designated primary egress."
        }

    # 2. Kitchen / Cooking Oil / Grease / Class K
    elif any(k in query for k in ["kitchen", "grease", "cooking oil", "fryer", "class k", "saponification", "cafeteria"]):
        return {
            "reply": (
                f"{live_context_alert}### 🍳 Tactical Protocol: Class K Commercial Cooking Oil Flashover (NFPA 10 & 96)\n\n"
                "**1. Suppression Mechanism (Saponification):**\n"
                "- **Mandated Agent:** **Wet Chemical Extinguishing Agent** (aqueous solution of potassium acetate, potassium carbonate, or potassium citrate).\n"
                "- **Reaction:** Forms a thick, soapy, heat-absorbing foam blanket across the hot oil surface (**saponification**), cutting off atmospheric oxygen and cooling the lipid pool below its auto-ignition temperature (typically 360°C / 680°F).\n"
                "- ⛔ **CRITICAL DANGER:** Applying water to hot boiling oil results in an immediate **steam explosion boilover**: 1 liter of water instantly expands to 1,700 liters of steam, carrying atomized burning grease across the room in a lethal fireball!\n\n"
                "**2. Mechanical Interlocks:**\n"
                "- Automated electrical shunt trips must instantly shut off gas supply solenoid valves and electric fryers.\n"
                "- Kitchen hood exhaust dampers close to prevent fire spreading into ductwork grease layers.\n\n"
                "**3. Evacuation Direction:**\n"
                "- Reroute all dining room personnel toward **Exit D (West Courtyard)** and away from Central Lobby smoke diffusion."
            ),
            "suggested_actions": ["Trigger Kitchen Wet Chemical", "Shut Gas Solenoid", "Ventilate West Courtyard"],
            "code_references": ["NFPA 96 (Commercial Cooking Operations)", "NFPA 10 (Portable Extinguishers, Class K)", "NFPA 17A (Wet Chemical Systems)"],
            "spoken_summary": "Class K grease fire requires wet chemical saponification. Never apply water. Evacuate via West Courtyard."
        }

    # 3. Chemical / Solvents / Lab / HazMat / Class B / Class D
    elif any(k in query for k in ["chemical", "solvent", "lab", "hazmat", "acetone", "hexane", "class b", "class d", "pyrophoric", "toxic"]):
        return {
            "reply": (
                f"{live_context_alert}### 🧪 Tactical Protocol: Class B Flammable Liquid & Class D Pyrophoric Hazard (NFPA 30 & 45)\n\n"
                "**1. Suppression Directives:**\n"
                "- **For Solvent Pool Fires (Acetone / Hexane):** Alcohol-Resistant Aqueous Film-Forming Foam (**AR-AFFF**) or dry chemical Purple-K.\n"
                "- **For Combustible Metals / Pyrophoric Reagents (Lithium Hydride):** **Class D Dry Powder** (Sodium Chloride / Copper based) applied with low-velocity applicator horn to gently smother without blowing burning particulate into the air.\n"
                "- ⛔ **RESTRICTION:** High-pressure water will cause violent solvent splattering and reacts exothermically with metal hydrides producing explosive hydrogen gas!\n\n"
                "**2. Atmospheric Containment:**\n"
                "- Emergency chemical negative-pressure scrubber fans ramp to 100% capacity (exhausting through HEPA / activated carbon beds).\n"
                "- Chemical blast dampers isolate Lab 4 from Central Reception.\n\n"
                "**3. Protective Equipment (PPE):**\n"
                "- First-responders must wear **Level B Self-Contained Breathing Apparatus (SCBA)** and vapor-protective chemical suits."
            ),
            "suggested_actions": ["Engage Chemical Scrubber", "Deploy Class D Powder", "Dispatch HazMat Task Force 1"],
            "code_references": ["NFPA 45 (Fire Protection for Chemical Labs)", "NFPA 30 (Flammable Liquids Code)", "OSHA 1910.1450 (Lab Safety)"],
            "spoken_summary": "Chemical laboratory incident requires AR-AFFF foam or Class D dry powder with Level B SCBA PPE."
        }

    # 4. Evacuation Routes / Exits / Dijkstra Pathfinding / Blocked corridors
    elif any(k in query for k in ["route", "exit", "evacuat", "dijkstra", "path", "corridor", "escape", "stairwell"]):
        routes_summary = ""
        if current_state and "floorplan" in current_state:
            routes = current_state["floorplan"].get("evacuation_routes", {})
            for r_id, r_info in routes.items():
                status_icon = "🟢" if r_info.get("safe") else "🔴"
                routes_summary += f"- {status_icon} **{r_info.get('room_name')}**: Assigned to `{r_info.get('exit_name')}` (~{r_info.get('estimated_evacuation_sec')}s)\n"
        else:
            routes_summary = "- 🟢 **All primary corridors clear**: Exit A (North), Exit B (East), Exit C (South), Exit D (West)."

        return {
            "reply": (
                f"{live_context_alert}### 🗺️ Dynamic Evacuation Intelligence & Spatial Pathfinding Engine\n\n"
                "Nexus Fire Safety AI uses graph-theoretic **Dijkstra's Shortest Path Algorithm** with dynamic environmental edge cost weights:\n\n"
                "$$\\text{Cost}(u, v) = \\text{Distance}(u, v) + \\alpha \\cdot \\text{Temp} + \\beta \\cdot \\text{Smoke} + \\gamma \\cdot \\text{FlameHazard}$$\n\n"
                "When a thermal sensor exceeds threshold (35°C+) or AI vision confirms smoke obscuration (>10%), the corridor edge weight is set to **$\\infty$**, instantly rerouting occupants in **< 100 milliseconds**.\n\n"
                f"**Current Zone Egress Status:**\n{routes_summary}\n\n"
                "**NFPA 101 Life Safety Code Compliance:**\n"
                "- Maximum allowable travel distance to nearest exit: 200 ft (un-sprinklered) / 250 ft (sprinklered).\n"
                "- Minimum egress width: 44 inches clear unobstructed walkway."
            ),
            "suggested_actions": ["View Evacuation Floorplan", "Verify Stairwell Pressurization", "Simulate Corridor Blockage"],
            "code_references": ["NFPA 101 (Life Safety Code)", "OSHA 1910.36 (Design & Construction of Exit Routes)"],
            "spoken_summary": "Dynamic Dijkstra pathfinding actively evaluates corridor safety. Occupants are automatically routed away from hazardous zones."
        }

    # 5. PA Broadcast / Public Address script / Announcement
    elif any(k in query for k in ["broadcast", "pa", "announcement", "script", "voice", "speech"]):
        active_hazard_text = "Server Room B" if scenario == "electrical_server" else "Cafeteria Kitchen" if scenario == "kitchen_flashover" else "Chemistry Lab 4" if scenario == "chemical_lab" else "designated zone"
        return {
            "reply": (
                "### 📢 Automated Emergency Public Address (PA) Script & Broadcast Directive\n\n"
                "**Official NFPA 72 Emergency Voice/Alarm Communications Service (EVACS) Script:**\n\n"
                f"> 🔊 *\"ATTENTION APEX BIOTECH BUILDING 4 OCCUPANTS. AN EMERGENCY INCIDENT HAS BEEN CONFIRMED IN {active_hazard_text.upper()}. DO NOT USE ELEVATORS. PLEASE PROCEED CALMLY ALONG ILLUMINATED GREEN EGRESS VECTORS TOWARD EXIT B (EAST STAIRWELL) AND EXIT D (WEST COURTYARD). RECEPTION SECURITY HAS CONFIRMED FIRST RESPONDERS ARE EN ROUTE. REMAIN CALM AND VACATE THE BUILDING.\"*\n\n"
                "**Acoustic Compliance Rules (NFPA 72 § 24.4.1):**\n"
                "- Speech intelligibility index (**STI**) must exceed **0.50** (Common Intelligibility Scale CIS > 0.70).\n"
                "- Sound pressure level must reach at least **15 dBA above ambient noise** (minimum 75 dBA in industrial/mechanical corridors)."
            ),
            "suggested_actions": ["Broadcast PA Over Facility Speakers", "Trigger Strobe Synchronization", "Notify Security Desk"],
            "code_references": ["NFPA 72 § 24 (Emergency Communications Systems)", "ISO 7240-19 (Voice Alarm Systems)"],
            "spoken_summary": "Attention building occupants: an emergency incident has been confirmed. Please proceed along illuminated green egress vectors to the nearest safe exit."
        }

    # 6. NFPA / Compliance / OSHA / Inspection / Extinguishers
    elif any(k in query for k in ["nfpa", "compliance", "osha", "audit", "extinguisher", "inspection", "clearance", "standard"]):
        return {
            "reply": (
                "### 📋 Life Safety & NFPA Code Compliance Architecture\n\n"
                "Nexus continuously audits the building against 4 primary life-safety regulatory frameworks:\n\n"
                "1. **NFPA 10 (Standard for Portable Fire Extinguishers):**\n"
                "   - 36 inches (3 ft) of clear, unobstructed frontal clearance required at all times.\n"
                "   - Monthly visual checks (pressure gauge needle in green pie, inspection tag intact, seal unbroken).\n"
                "   - Hydrostatic pressure re-testing every 5 or 12 years depending on cylinder alloy.\n\n"
                "2. **NFPA 72 (National Fire Alarm & Signaling Code):**\n"
                "   - Mandates the **Temporal-3 audible tone** (0.5s on, 0.5s off, 0.5s on, 0.5s off, 0.5s on, 1.5s pause).\n"
                "   - Synchronized strobe flashing (1 Hz rate, 15 to 110 candela) to prevent photo-epileptic seizures.\n\n"
                "3. **NFPA 101 (Life Safety Code) & OSHA 1910.36:**\n"
                "   - Self-closing, positive-latching 90-minute fire-rated doors on all egress stairwells.\n"
                "   - Zero dead-end corridors exceeding 20 feet.\n"
                "   - Emergency backup battery lighting sustaining 90 minutes minimum runtime during utility outage."
            ),
            "suggested_actions": ["Open Compliance Ledger", "Export Life Safety Audit Report", "Run Extinguisher Clearance Scan"],
            "code_references": ["NFPA 10", "NFPA 72", "NFPA 101", "OSHA 1910.36"],
            "spoken_summary": "Building compliance requires 36 inches extinguisher clearance, NFPA 72 Temporal-3 audibility, and 90-minute battery emergency lighting."
        }

    # 7. Flashover / Thermal Physics / Fire Dynamics
    elif any(k in query for k in ["flashover", "physics", "thermal", "temperature", "heat index", "spread"]):
        return {
            "reply": (
                "### 🔥 Fire Dynamics & Predictive Flashover Physics Model\n\n"
                "**Flashover** is the near-simultaneous thermal ignition of all exposed combustible material in an enclosed compartment:\n\n"
                "$$\\dot{Q}_{\\text{fo}} = 750 \\cdot \\left( A_T \\cdot A_V \\cdot \\sqrt{H_V} \\right)^{1/2} \\quad [\\text{kW}]$$\n\n"
                "- **Critical Threshold:** Ceiling layer temperatures exceeding **500°C to 600°C (932°F - 1112°F)** or radiant heat flux at floor level exceeding **20 kW/m²**.\n"
                "- **Early Warning Indicators Tracked by Nexus:**\n"
                "  1. Thermal rate-of-rise exceeding **8.3°C/minute (15°F/min)**.\n"
                "  2. Optical smoke obscuration exceeding **15%/ft** with rapid floor-to-ceiling stratification.\n"
                "  3. Thermal roll-over licking across ceiling bar joists detected by Sentinel Vision optical flow.\n\n"
                "When flashover probability reaches >60%, Nexus initiates automated room isolation and pre-action suppression flooding."
            ),
            "suggested_actions": ["View Thermal Trend Stream", "Check Ceiling Hotspot Sensor", "Inspect Flashover Probability"],
            "code_references": ["SFPE Handbook of Fire Protection Engineering", "NFPA 921 (Fire and Explosion Investigations)"],
            "spoken_summary": "Flashover occurs when compartment temperatures exceed 500 degrees Celsius. Nexus tracks rate-of-rise to trigger pre-emptive suppression."
        }

    # Default / General Query Response
    else:
        return {
            "reply": (
                f"{live_context_alert}### 🤖 Nexus Fire Safety AI Incident Advisor\n\n"
                f"**System Status:** Defcon {threat.get('defcon_level', 4)} ({severity}) | Monitored Nodes: 28 IoT Thermal & Vision Arrays.\n\n"
                f"Regarding your query: *\"{user_query}\"*\n\n"
                "**Key Operational Directives:**\n"
                "1. **Life Safety First (NFPA 101):** Occupant evacuation along dynamic green-lit Dijkstra routes takes precedence over asset preservation.\n"
                "2. **Agent Matching (NFPA 10/2001):** Verify fire classification prior to manual or automated suppression discharge (Class A: Water; Class B: Foam/Dry Chem; Class C: FM-200 Clean Agent; Class D: Dry Powder; Class K: Wet Chemical).\n"
                "3. **First-Responder Coordination (NFPA 901):** Autonomous CAD dispatch feeds are live on VHF Channel 4 and Siamese Standpipe connections are primed.\n\n"
                "Ask me about specific fire classes, evacuation strategies, NFPA regulations, or live scenario simulations!"
            ),
            "suggested_actions": ["Review Evacuation Map", "Test WebCam Sentinel", "Inspect Incident Action Plan"],
            "code_references": ["NFPA 1", "NFPA 101", "NFPA 72"],
            "spoken_summary": "Nexus Fire Safety AI is operational. All life safety systems, dynamic pathfinding, and automated dispatch channels are ready."
        }


def evaluate_drill_decision(drill_data):
    """
    Evaluates participant responses in the interactive Fire Commander Drill trainer.
    Calculates numerical score (0-100), detailed tactical breakdown, and badge.
    """
    scenario = drill_data.get("scenario", "electrical_server")
    suppression = drill_data.get("suppression", "").lower()
    hvac = drill_data.get("hvac", "").lower()
    egress = drill_data.get("egress", "").lower()

    score = 0
    feedback = []

    # 1. Suppression Evaluation
    if scenario == "electrical_server":
        if "fm200" in suppression or "clean_agent" in suppression:
            score += 35
            feedback.append("✅ Suppression (35/35): Perfect! FM-200 / Clean Agent suppresses Class C fire without electrical conductivity or residue.")
        elif "water" in suppression:
            score += 0
            feedback.append("❌ Suppression (0/35): CATASTROPHIC! Applying water to 480V server racks risks explosive short-circuit arcs and electrocution!")
        else:
            score += 15
            feedback.append("⚠️ Suppression (15/35): Sub-optimal. Dry chemical will control flame but corrodes expensive enterprise hardware.")
    elif scenario == "kitchen_flashover":
        if "wet_chem" in suppression or "potassium" in suppression:
            score += 35
            feedback.append("✅ Suppression (35/35): Excellent! Wet chemical potassium acetate initiates saponification, safely cooling grease.")
        elif "water" in suppression:
            score += 0
            feedback.append("❌ Suppression (0/35): LETHAL! Water into boiling grease causes an explosive steam fireball!")
        else:
            score += 18
            feedback.append("⚠️ Suppression (18/35): Moderate. Standard CO2 or powder may temporarily knock down flame but oil easily re-ignites.")
    else: # chem lab
        if "foam" in suppression or "dry_powder" in suppression:
            score += 35
            feedback.append("✅ Suppression (35/35): Correct. AR-AFFF Foam / Class D Powder smothers solvent pool fire without water reactivity.")
        elif "water" in suppression:
            score += 5
            feedback.append("❌ Suppression (5/35): Dangerous! Water causes solvent pool spreading and violent exothermic reaction with hydrides.")
        else:
            score += 20
            feedback.append("⚠️ Suppression (20/35): Partial containment.")

    # 2. HVAC & Damper Evaluation
    if "seal" in hvac or "recirc_off" in hvac or "isolate" in hvac:
        score += 35
        feedback.append("✅ Ventilation (35/35): Correct. Sealing dampers prevents toxic smoke propagation to adjacent corridors.")
    elif "exhaust" in hvac:
        score += 20
        feedback.append("⚠️ Ventilation (20/35): Exhausting helps smoke extraction but may draw fire toward ductwork if not fire-damper protected.")
    else:
        score += 5
        feedback.append("❌ Ventilation (5/35): Leaving HVAC in normal cycle fans sparks and disseminates toxic gas across the building.")

    # 3. Egress Routing Evaluation
    if "east" in egress or "dock" in egress or "courtyard" in egress:
        score += 30
        feedback.append("✅ Egress Routing (30/30): Optimal escape vector selected away from hazardous smoke corridor.")
    else:
        score += 10
        feedback.append("⚠️ Egress Routing (10/30): Route traverses compromised or smoke-adjacent junctions.")

    # Commander Ranking
    if score >= 90:
        rank = "Master Incident Commander (5 Stars)"
    elif score >= 75:
        rank = "Tactical Captain (4 Stars)"
    elif score >= 50:
        rank = "Safety Lieutenant (3 Stars)"
    else:
        rank = "Incident Recruit (Needs Retraining)"

    return {
        "score": score,
        "rank": rank,
        "scenario": scenario,
        "feedback": feedback,
        "certified_date": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def generate_iap_report(state):
    """
    Generates a full NFPA 901 Incident Action Plan (IAP) formatted document.
    """
    scenario = state.get("scenario", "normal")
    threat = state.get("threat", {})
    sensors = state.get("sensors", {})
    occupants = state.get("occupant_status", {})
    tactical = threat.get("tactical", {})
    cad = tactical.get("dispatch_cad", {})

    report_id = f"IAP-{int(time.time())}"
    timestamp = time.strftime("%B %d, %Y - %H:%M:%S EST")

    return {
        "report_id": report_id,
        "timestamp": timestamp,
        "incident_name": f"Nexus Operation: {cad.get('box_code', 'Apex BioTech Facility')}",
        "operational_period": "Period 1 (00:00 - 02:00 Hours On-Scene)",
        "facility": "Apex BioTech Research Facility, Building 4",
        "command_staff": {
            "incident_commander": "Autonomous Nexus AI Commander v3.4 (Supervised by Fire Marshal M. Reynolds)",
            "safety_officer": "AI Environmental Sensor Mesh (28 Nodes)",
            "operations_chief": "Battalion Chief 2 (On-Scene Ingress)"
        },
        "tactical_objectives": [
            f"1. Contain active {tactical.get('fire_class', 'Class A')} combustion via {tactical.get('primary_agent', 'Automatic Sprinklers')}.",
            "2. Maintain positive pressure in East and West egress stairwells.",
            f"3. Account for all {occupants.get('total', 67)} registered building occupants ({occupants.get('evacuated', 0)} evacuated to date).",
            f"4. Enforce strict agent prohibition: {tactical.get('avoid_agent', 'None')}."
        ],
        "hazard_ledger": {
            "peak_thermal": f"{threat.get('thermal_index_c', 21.4)}°C",
            "smoke_obscuration": f"{threat.get('smoke_obscuration_pct', 0.1)}%/ft",
            "co_density": f"{threat.get('co_density_ppm', 2.0)} ppm",
            "flashover_risk": f"{threat.get('flashover_risk_pct', 2)}%",
            "flame_confirmed": threat.get("flame_detected", False)
        },
        "logistics": {
            "hydrant": cad.get("nearest_hydrant", "Hydrant #12 (45m North Entrance, 140 PSI)"),
            "assigned_units": cad.get("recommended_units", ["Engine 12", "Truck 4", "HazMat 1", "Battalion Chief 2"]),
            "radio_tactical_channel": "Tac-4 (VHF 154.280 MHz)",
            "staging_area": "North Parking Apron Lot B"
        }
    }
