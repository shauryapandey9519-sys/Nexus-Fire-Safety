"""
Nexus Fire Safety AI - Dynamic Spatial Pathfinding & Floorplan Engine
Implements graph-based architectural mapping and Dijkstra's algorithm to calculate
real-time, obstacle-avoiding evacuation routes during fire/smoke emergencies.
"""

import math
import heapq

# Floorplan geometry definition (Level 1 - Apex Research Facility Building 4)
# Coordinates on a normalized 1000 x 600 canvas
ROOMS = {
    "server_b": {
        "id": "server_b",
        "name": "Server Room B (Data Center)",
        "floor": 1,
        "x": 60, "y": 60, "w": 220, "h": 160,
        "color": "#1e293b",
        "default_occupancy": 3,
        "hazard_type": "Class C Electrical",
        "exit_point": (280, 140)
    },
    "chem_lab": {
        "id": "chem_lab",
        "name": "Chemistry Lab 4",
        "floor": 1,
        "x": 340, "y": 60, "w": 280, "h": 160,
        "color": "#1e293b",
        "default_occupancy": 8,
        "hazard_type": "Class B Chemical Vapor",
        "exit_point": (480, 220)
    },
    "executive": {
        "id": "executive",
        "name": "Executive Briefing Suite",
        "floor": 1,
        "x": 680, "y": 60, "w": 260, "h": 160,
        "color": "#1e293b",
        "default_occupancy": 12,
        "hazard_type": "Class A Ordinary",
        "exit_point": (680, 140)
    },
    "cafeteria": {
        "id": "cafeteria",
        "name": "Cafeteria & Commercial Kitchen",
        "floor": 1,
        "x": 60, "y": 360, "w": 260, "h": 180,
        "color": "#1e293b",
        "default_occupancy": 18,
        "hazard_type": "Class K Commercial Cooking Oil",
        "exit_point": (320, 420)
    },
    "open_workspace": {
        "id": "open_workspace",
        "name": "Open Workspace (Engineering)",
        "floor": 1,
        "x": 380, "y": 360, "w": 320, "h": 180,
        "color": "#1e293b",
        "default_occupancy": 24,
        "hazard_type": "Class A Ordinary",
        "exit_point": (540, 360)
    },
    "mechanical": {
        "id": "mechanical",
        "name": "Mechanical & HVAC Substation",
        "floor": 1,
        "x": 760, "y": 360, "w": 180, "h": 180,
        "color": "#1e293b",
        "default_occupancy": 2,
        "hazard_type": "Class C / Heavy Machinery",
        "exit_point": (760, 420)
    },
    "central_lobby": {
        "id": "central_lobby",
        "name": "Central Atrium & Security Reception",
        "floor": 1,
        "x": 380, "y": 250, "w": 240, "h": 80,
        "color": "#0f172a",
        "default_occupancy": 5,
        "hazard_type": "Assembly Egress Zone",
        "exit_point": (500, 250)
    }
}

# Designated Emergency Exits
EXITS = {
    "exit_north": {
        "id": "exit_north",
        "name": "Exit A - North Main Concourse",
        "pos": (500, 30),
        "status": "CLEAR",
        "width_inches": 72,
        "outdoor_safe_point": (500, 5)
    },
    "exit_east": {
        "id": "exit_east",
        "name": "Exit B - East Fire Stairwell",
        "pos": (970, 270),
        "status": "CLEAR",
        "width_inches": 48,
        "outdoor_safe_point": (990, 270)
    },
    "exit_south": {
        "id": "exit_south",
        "name": "Exit C - South Loading Dock & Yard",
        "pos": (540, 570),
        "status": "CLEAR",
        "width_inches": 60,
        "outdoor_safe_point": (540, 595)
    },
    "exit_west": {
        "id": "exit_west",
        "name": "Exit D - West Courtyard Escape",
        "pos": (30, 270),
        "status": "CLEAR",
        "width_inches": 48,
        "outdoor_safe_point": (10, 270)
    }
}

# Corridors & Waypoints Graph
WAYPOINTS = {
    # Main hallway nodes
    "node_w1": (180, 270),
    "node_w2": (320, 270),
    "node_center": (500, 270),
    "node_e1": (680, 270),
    "node_e2": (840, 270),
    
    # North corridor junctions
    "node_n_server": (280, 220),
    "node_n_chem": (480, 220),
    "node_n_exit": (500, 45),
    "node_n_exec": (680, 220),
    
    # South corridor junctions
    "node_s_cafe": (320, 360),
    "node_s_work": (540, 360),
    "node_s_exit": (540, 560),
    "node_s_mech": (760, 360),
    
    # Exits directly
    "exit_w": (30, 270),
    "exit_e": (970, 270),
}

# Baseline Edge Connections with natural pixel distance
BASE_EDGES = [
    # West wing
    ("exit_w", "node_w1"),
    ("node_w1", "node_w2"),
    ("node_w1", "node_n_server"),
    ("node_w2", "node_center"),
    ("node_w2", "node_s_cafe"),
    
    # Center & North exit
    ("node_center", "node_n_chem"),
    ("node_n_chem", "node_n_exit"),
    ("node_center", "node_s_work"),
    ("node_center", "node_e1"),
    
    # East wing & East exit
    ("node_e1", "node_n_exec"),
    ("node_e1", "node_e2"),
    ("node_e1", "node_s_work"),
    ("node_e2", "node_s_mech"),
    ("node_e2", "exit_e"),
    
    # South spine & South exit
    ("node_s_cafe", "node_s_work"),
    ("node_s_work", "node_s_exit"),
    ("node_s_work", "node_s_mech"),
    
    # Room door links
    ("server_b", "node_n_server"),
    ("chem_lab", "node_n_chem"),
    ("executive", "node_n_exec"),
    ("cafeteria", "node_s_cafe"),
    ("open_workspace", "node_s_work"),
    ("mechanical", "node_s_mech"),
    ("central_lobby", "node_center")
]

def euclidean_dist(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

class FloorplanEngine:
    def __init__(self):
        self.rooms = ROOMS
        self.exits = EXITS
        self.waypoints = WAYPOINTS
        self.base_edges = BASE_EDGES
        self.blocked_nodes = set()
        self.hazard_zones = {} # room_id -> {severity, temp, smoke, flame}

    def get_node_pos(self, node_id):
        if node_id in self.waypoints:
            return self.waypoints[node_id]
        if node_id in self.rooms:
            return self.rooms[node_id]["exit_point"]
        if node_id in self.exits:
            return self.exits[node_id]["pos"]
        return (500, 300)

    def set_hazards(self, hazard_dict):
        """
        hazard_dict: { "server_b": {"severity": "CRITICAL", "blocked": True}, ... }
        """
        self.hazard_zones = hazard_dict
        self.blocked_nodes = set()
        
        for room_id, info in hazard_dict.items():
            if info.get("blocked", False) or info.get("severity") in ["HIGH", "CRITICAL"]:
                self.blocked_nodes.add(room_id)
                # If server room is on fire, west junction has heavy smoke hazard
                if room_id == "server_b":
                    self.blocked_nodes.add("node_n_server")
                elif room_id == "cafeteria":
                    self.blocked_nodes.add("node_s_cafe")
                elif room_id == "chem_lab":
                    self.blocked_nodes.add("node_n_chem")
                elif room_id == "executive":
                    self.blocked_nodes.add("node_n_exec")
                elif room_id == "open_workspace":
                    self.blocked_nodes.add("node_s_work")
                elif room_id == "mechanical":
                    self.blocked_nodes.add("node_s_mech")

    def build_graph(self):
        graph = {}
        # Ensure all nodes exist
        all_nodes = set(list(self.waypoints.keys()) + list(self.rooms.keys()) + list(self.exits.keys()))
        for n in all_nodes:
            graph[n] = []

        for u, v in self.base_edges:
            p1 = self.get_node_pos(u)
            p2 = self.get_node_pos(v)
            dist = euclidean_dist(p1, p2)
            
            # Penalize or block dangerous paths
            cost_u_v = dist
            cost_v_u = dist
            
            if u in self.blocked_nodes or v in self.blocked_nodes:
                cost_u_v = 1e9 # practically impassable
                cost_v_u = 1e9
                
            graph[u].append((v, cost_u_v))
            graph[v].append((u, cost_v_u))

        return graph

    def dijkstra(self, start_node, target_nodes):
        graph = self.build_graph()
        distances = {node: float('inf') for node in graph}
        previous = {node: None for node in graph}
        distances[start_node] = 0
        
        pq = [(0, start_node)]
        
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            if current_dist > distances[current_node]:
                continue
            if current_node in target_nodes and current_dist < 1e8:
                # Found reachable exit
                break
                
            for neighbor, weight in graph.get(current_node, []):
                distance = current_dist + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))

        # Find best exit among targets
        best_exit = None
        min_dist = float('inf')
        for target in target_nodes:
            if distances[target] < min_dist and distances[target] < 1e8:
                min_dist = distances[target]
                best_exit = target

        if not best_exit:
            # If completely trapped, find lowest penalty fallback
            for target in target_nodes:
                if distances[target] < min_dist:
                    min_dist = distances[target]
                    best_exit = target

        # Reconstruct path
        path = []
        curr = best_exit
        while curr:
            path.append(curr)
            curr = previous.get(curr)
        path.reverse()

        # Convert path to coordinates
        coords = [self.get_node_pos(n) for n in path]
        return {
            "path_nodes": path,
            "waypoints": coords,
            "target_exit": best_exit,
            "total_distance_px": round(min_dist, 1) if min_dist < 1e8 else -1,
            "status": "SAFE_ROUTE" if min_dist < 1e8 else "BLOCKED_HAZARD"
        }

    def calculate_all_evacuation_routes(self):
        exit_keys = list(self.exits.keys()) + ["exit_w", "exit_e", "node_n_exit", "node_s_exit"]
        results = {}
        for room_id in self.rooms:
            res = self.dijkstra(room_id, ["exit_w", "exit_e", "node_n_exit", "node_s_exit"])
            # Map logical exit node to exit name
            exit_name = "Exit A (North Concourse)"
            if res["target_exit"] in ["exit_e"]:
                exit_name = "Exit B (East Stairwell)"
            elif res["target_exit"] in ["node_s_exit"]:
                exit_name = "Exit C (South Loading Dock)"
            elif res["target_exit"] in ["exit_w"]:
                exit_name = "Exit D (West Courtyard)"

            results[room_id] = {
                "room_name": self.rooms[room_id]["name"],
                "exit_name": exit_name,
                "waypoints": res["waypoints"],
                "path_nodes": res["path_nodes"],
                "safe": res["status"] == "SAFE_ROUTE",
                "estimated_evacuation_sec": max(12, int(res["total_distance_px"] * 0.08)) if res["status"] == "SAFE_ROUTE" else 999
            }
        return results

    def get_floorplan_state(self):
        routes = self.calculate_all_evacuation_routes()
        return {
            "floor": 1,
            "facility_name": "Apex BioTech Research Center - Building 4",
            "canvas_bounds": {"w": 1000, "h": 600},
            "rooms": self.rooms,
            "exits": self.exits,
            "waypoints": self.waypoints,
            "edges": self.base_edges,
            "blocked_nodes": list(self.blocked_nodes),
            "hazard_zones": self.hazard_zones,
            "evacuation_routes": routes
        }

floorplan_engine = FloorplanEngine()

if __name__ == "__main__":
    floorplan_engine.set_hazards({"server_b": {"severity": "CRITICAL", "blocked": True}})
    routes = floorplan_engine.calculate_all_evacuation_routes()
    print("Evacuation route from Server Room B:", routes["server_b"]["exit_name"], routes["server_b"]["safe"])
    print("Evacuation route from Open Workspace:", routes["open_workspace"]["exit_name"], routes["open_workspace"]["safe"])
