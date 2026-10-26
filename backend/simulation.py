"""
Nexus Fire Safety AI - Emergency Incident & Environmental Simulation Manager
Coordinates real-time IoT sensor telemetry generation, thermal/smoke diffusion physics,
and scenario transitions.
"""

import time
import math
import random
from .pathfinding import floorplan_engine
from .ai_engine import evaluate_threat, analyze_camera_feed
from .database import add_log, get_connection

class SimulationManager:
    def __init__(self):
        self.scenario = "normal"  # normal, electrical_server, kitchen_flashover, chemical_lab
        self.started_at = time.time()
        self.scenario_start_time = None
        self.history = [] # holds rolling telemetry history for charts
        self.occupant_status = {
            "total": 67,
            "evacuated": 0,
            "in_transit": 0,
            "sheltered": 67
        }
        self.init_baseline_sensors()

    def init_baseline_sensors(self):
        self.sensors = {
            "server_b": {
                "name": "Server Room B",
                "temp": 21.4,
                "smoke": 0.08,
                "co": 2.1,
                "voc": 12,
                "sprinkler": "STANDBY",
                "sprinkler_psi": 124,
                "hvac_cfm": 1450,
                "sound_dba": 62,
                "flame_detected": False,
                "status": "NORMAL"
            },
            "chem_lab": {
                "name": "Chemistry Lab 4",
                "temp": 22.0,
                "smoke": 0.12,
                "co": 3.4,
                "voc": 45,
                "sprinkler": "STANDBY",
                "sprinkler_psi": 122,
                "hvac_cfm": 2100,
                "sound_dba": 58,
                "flame_detected": False,
                "status": "NORMAL"
            },
            "cafeteria": {
                "name": "Cafeteria & Kitchen",
                "temp": 23.8,
                "smoke": 0.25,
                "co": 4.8,
                "voc": 28,
                "sprinkler": "STANDBY",
                "sprinkler_psi": 120,
                "hvac_cfm": 1800,
                "sound_dba": 68,
                "flame_detected": False,
                "status": "NORMAL"
            },
            "open_workspace": {
                "name": "Open Workspace",
                "temp": 21.8,
                "smoke": 0.05,
                "co": 1.9,
                "voc": 15,
                "sprinkler": "STANDBY",
                "sprinkler_psi": 121,
                "hvac_cfm": 1950,
                "sound_dba": 54,
                "flame_detected": False,
                "status": "NORMAL"
            },
            "executive": {
                "name": "Executive Briefing Suite",
                "temp": 21.2,
                "smoke": 0.04,
                "co": 1.5,
                "voc": 8,
                "sprinkler": "STANDBY",
                "sprinkler_psi": 125,
                "hvac_cfm": 1200,
                "sound_dba": 46,
                "flame_detected": False,
                "status": "NORMAL"
            },
            "mechanical": {
                "name": "Mechanical & HVAC Substation",
                "temp": 25.1,
                "smoke": 0.15,
                "co": 4.1,
                "voc": 35,
                "sprinkler": "STANDBY",
                "sprinkler_psi": 122,
                "hvac_cfm": 3400,
                "sound_dba": 78,
                "flame_detected": False,
                "status": "NORMAL"
            },
            "central_lobby": {
                "name": "Central Reception Lobby",
                "temp": 22.1,
                "smoke": 0.06,
                "co": 2.0,
                "voc": 10,
                "sprinkler": "STANDBY",
                "sprinkler_psi": 123,
                "hvac_cfm": 1600,
                "sound_dba": 56,
                "flame_detected": False,
                "status": "NORMAL"
            }
        }

    def set_scenario(self, scenario_name):
        valid = ["normal", "electrical_server", "kitchen_flashover", "chemical_lab"]
        if scenario_name not in valid:
            scenario_name = "normal"
        self.scenario = scenario_name
        self.scenario_start_time = time.time() if scenario_name != "normal" else None

        if scenario_name == "normal":
            self.init_baseline_sensors()
            floorplan_engine.set_hazards({})
            self.occupant_status = {"total": 67, "evacuated": 0, "in_transit": 0, "sheltered": 67}
            add_log("INFO", "Scenario Engine", "System reset to normal baseline. All zones secured.")
        elif scenario_name == "electrical_server":
            floorplan_engine.set_hazards({"server_b": {"severity": "CRITICAL", "blocked": True}})
            add_log("ALARM", "Vision AI", "Class C electrical ignition detected in Server Room B! Clean Agent primed.")
        elif scenario_name == "kitchen_flashover":
            floorplan_engine.set_hazards({"cafeteria": {"severity": "CRITICAL", "blocked": True}})
            add_log("ALARM", "Thermal Array", "Rapid thermal rate-of-rise in Commercial Kitchen! Class K grease fire.")
        elif scenario_name == "chemical_lab":
            floorplan_engine.set_hazards({"chem_lab": {"severity": "CRITICAL", "blocked": True}})
            add_log("ALARM", "VOC Spectrometer", "Toxic vapor explosion & Class B flashover in Chemistry Lab 4!")

        return self.get_state()

    def update_tick(self):
        """
        Advances environmental simulation state based on active scenario and elapsed time.
        """
        now = time.time()
        elapsed = (now - self.scenario_start_time) if self.scenario_start_time else 0

        # Small ambient jitter for realism
        for r_id, s in self.sensors.items():
            if self.scenario == "normal" or r_id not in ["server_b", "cafeteria", "chem_lab"]:
                # Ambient fluctuation
                s["temp"] = max(18.0, min(28.0, s["temp"] + random.uniform(-0.15, 0.15)))
                s["smoke"] = max(0.01, min(0.8, s["smoke"] + random.uniform(-0.01, 0.01)))
                s["co"] = max(0.5, min(6.0, s["co"] + random.uniform(-0.1, 0.1)))
                s["voc"] = max(5, min(50, s["voc"] + random.randint(-1, 1)))

        # Scenario specific physics
        if self.scenario == "electrical_server":
            target_room = self.sensors["server_b"]
            # Temperature rises quickly to 85°C+
            growth = min(1.0, elapsed / 20.0)
            target_room["temp"] = 22.0 + (74.0 * growth) + random.uniform(-0.8, 0.8)
            target_room["smoke"] = 0.1 + (58.0 * growth) + random.uniform(-1.0, 1.0)
            target_room["co"] = 3.0 + (92.0 * growth) + random.uniform(-1.5, 1.5)
            target_room["flame_detected"] = True
            target_room["status"] = "CRITICAL FIRE"
            target_room["sprinkler"] = "FM-200 DISCHARGE"
            target_room["sound_dba"] = 104 # NFPA Temporal-3 horn active
            
            # Smoke diffusion to adjacent open workspace and west corridor
            if elapsed > 10:
                self.sensors["open_workspace"]["smoke"] = 0.1 + min(12.0, (elapsed - 10) * 0.8)
                self.sensors["open_workspace"]["co"] = 2.0 + min(18.0, (elapsed - 10) * 0.9)
                self.sensors["open_workspace"]["status"] = "SMOKE SPREAD"

        elif self.scenario == "kitchen_flashover":
            target_room = self.sensors["cafeteria"]
            growth = min(1.0, elapsed / 18.0)
            target_room["temp"] = 24.0 + (82.0 * growth) + random.uniform(-1.0, 1.0)
            target_room["smoke"] = 0.2 + (72.0 * growth) + random.uniform(-1.2, 1.2)
            target_room["co"] = 4.0 + (110.0 * growth) + random.uniform(-2.0, 2.0)
            target_room["flame_detected"] = True
            target_room["status"] = "CRITICAL FIRE"
            target_room["sprinkler"] = "WET CHEMICAL SYSTEM"
            target_room["sound_dba"] = 106

            if elapsed > 8:
                self.sensors["central_lobby"]["smoke"] = 0.1 + min(8.0, (elapsed - 8) * 0.6)
                self.sensors["central_lobby"]["status"] = "LIGHT SMOKE"

        elif self.scenario == "chemical_lab":
            target_room = self.sensors["chem_lab"]
            growth = min(1.0, elapsed / 15.0)
            target_room["temp"] = 22.0 + (68.0 * growth) + random.uniform(-0.7, 0.7)
            target_room["smoke"] = 0.1 + (45.0 * growth) + random.uniform(-0.8, 0.8)
            target_room["co"] = 3.0 + (60.0 * growth) + random.uniform(-1.0, 1.0)
            target_room["voc"] = 45 + int(480 * growth)
            target_room["flame_detected"] = True
            target_room["status"] = "HAZMAT FIRE"
            target_room["sprinkler"] = "DRY CHEMICAL / N2 PURGE"
            target_room["sound_dba"] = 102

        # Update simulated evacuation head-count if scenario is active
        if self.scenario != "normal":
            rate = min(67, int(elapsed * 2.2))
            self.occupant_status["evacuated"] = rate
            self.occupant_status["in_transit"] = max(0, min(24, 67 - rate))
            self.occupant_status["sheltered"] = max(0, 67 - self.occupant_status["evacuated"] - self.occupant_status["in_transit"])

        # Record history sample
        self.record_history()

    def record_history(self):
        max_temp = max(s["temp"] for s in self.sensors.values())
        max_smoke = max(s["smoke"] for s in self.sensors.values())
        max_co = max(s["co"] for s in self.sensors.values())
        
        point = {
            "time": time.strftime("%H:%M:%S"),
            "max_temp": round(max_temp, 1),
            "max_smoke": round(max_smoke, 1),
            "max_co": round(max_co, 1)
        }
        self.history.append(point)
        if len(self.history) > 25:
            self.history.pop(0)

    def set_room_hazard(self, room_id, temp=75.0, smoke=35.0, flame=True):
        if room_id in self.sensors:
            self.sensors[room_id]["temp"] = float(temp)
            self.sensors[room_id]["smoke"] = float(smoke)
            self.sensors[room_id]["flame_detected"] = bool(flame)
            self.sensors[room_id]["status"] = "MANUAL INJECTION"
            self.scenario = f"hazard_{room_id}"
            self.scenario_start_time = time.time()
            hazards = {room_id: {"severity": "CRITICAL", "blocked": True}}
            floorplan_engine.set_hazards(hazards)
            add_log("ALARM", "Manual Injection", f"Custom thermal/smoke hazard injected into {self.sensors[room_id]['name']} ({temp}°C, {smoke}% smoke)")
        return self.get_state()

    def clear_room_hazard(self, room_id):
        if room_id in self.sensors:
            self.sensors[room_id]["temp"] = 21.5
            self.sensors[room_id]["smoke"] = 0.05
            self.sensors[room_id]["flame_detected"] = False
            self.sensors[room_id]["status"] = "NORMAL"
            floorplan_engine.set_hazards({})
            self.scenario = "normal"
            add_log("INFO", "Manual Control", f"Hazard cleared in {self.sensors[room_id]['name']}")
        return self.get_state()

    def get_state(self):
        max_temp = max(s["temp"] for s in self.sensors.values())
        max_smoke = max(s["smoke"] for s in self.sensors.values())
        max_co = max(s["co"] for s in self.sensors.values())
        flame_any = any(s["flame_detected"] for s in self.sensors.values())

        active_room_map = {
            "electrical_server": "server_b",
            "kitchen_flashover": "cafeteria",
            "chemical_lab": "chem_lab",
            "normal": "normal"
        }
        active_room = active_room_map.get(self.scenario, "normal")

        threat = evaluate_threat({
            "max_temp": max_temp,
            "max_smoke": max_smoke,
            "max_co": max_co,
            "flame_detected": flame_any,
            "active_room": active_room
        })

        cameras = {
            "cam_server": analyze_camera_feed("cam_server", self.scenario),
            "cam_cafe": analyze_camera_feed("cam_cafe", self.scenario),
            "cam_lab": analyze_camera_feed("cam_lab", self.scenario),
            "cam_lobby": analyze_camera_feed("cam_lobby", self.scenario)
        }

        floorplan_state = floorplan_engine.get_floorplan_state()

        return {
            "scenario": self.scenario,
            "uptime_seconds": int(time.time() - self.started_at),
            "threat": threat,
            "sensors": self.sensors,
            "occupant_status": self.occupant_status,
            "cameras": cameras,
            "floorplan": floorplan_state,
            "history": self.history
        }

simulation = SimulationManager()
