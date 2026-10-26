/**
 * Nexus Fire Safety AI - Frontend Application Core
 * Manages Real-time SSE Streams, Floorplan Pathfinding Canvas, Web Audio NFPA 72 Siren,
 * Computer Vision Sentinel (Simulated + Live WebCam), Sensor Charts, and Compliance Audits.
 */

// Application State
const state = {
  currentTab: "hub",
  scenario: "normal",
  threat: {
    severity: "NORMAL",
    defcon_level: 4,
    risk_score: 4,
    thermal_index_c: 21.4,
    smoke_obscuration_pct: 0.1,
    co_density_ppm: 2.1,
    flame_detected: false,
    flashover_risk_pct: 2,
    tactical: {}
  },
  sensors: {},
  occupants: { total: 67, evacuated: 0, in_transit: 0, sheltered: 67 },
  cameras: {},
  floorplan: null,
  history: [],
  selectedRoom: "server_b",
  sirenActive: false,
  webcamActive: false,
  webcamStream: null
};

// ==========================================
// 1. Audio Engine (NFPA 72 Temporal-3 Alarm)
// ==========================================
class AlarmAudioEngine {
  constructor() {
    this.audioCtx = null;
    this.isPlaying = false;
    this.timer = null;
    this.speechSynthesis = window.speechSynthesis;
    this.lastSpokenScenario = null;
  }

  initContext() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContext();
    }
    if (this.audioCtx.state === "suspended") {
      this.audioCtx.resume();
    }
  }

  playNFPA72Pulse() {
    if (!this.isPlaying || !this.audioCtx) return;
    const now = this.audioCtx.currentTime;
    
    // Temporal-3 Pattern: 3 pulses of 0.5s on, 0.5s off, followed by 1.5s silence
    const pulseDuration = 0.5;
    const pulseGap = 0.5;
    const toneFreq = 960; // Standard NFPA 72 piercing alert frequency

    for (let i = 0; i < 3; i++) {
      const startTime = now + i * (pulseDuration + pulseGap);
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(toneFreq, startTime);
      
      // Pulse shape
      gain.gain.setValueAtTime(0, startTime);
      gain.gain.linearRampToValueAtTime(0.18, startTime + 0.04);
      gain.gain.setValueAtTime(0.18, startTime + pulseDuration - 0.04);
      gain.gain.linearRampToValueAtTime(0, startTime + pulseDuration);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start(startTime);
      osc.stop(startTime + pulseDuration);
    }

    // Schedule next cycle in 4 seconds
    this.timer = setTimeout(() => {
      this.playNFPA72Pulse();
    }, 4000);
  }

  startAlarm() {
    this.initContext();
    if (this.isPlaying) return;
    this.isPlaying = true;
    this.playNFPA72Pulse();
    updateSirenUI(true);
  }

  stopAlarm() {
    this.isPlaying = false;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    updateSirenUI(false);
  }

  toggleAlarm() {
    if (this.isPlaying) {
      this.stopAlarm();
    } else {
      this.startAlarm();
    }
  }

  playPAChime(callback) {
    this.initContext();
    if (!this.audioCtx) {
      if (callback) callback();
      return;
    }
    const now = this.audioCtx.currentTime;
    // Chime tone 1: 587.33 Hz (D5)
    const osc1 = this.audioCtx.createOscillator();
    const gain1 = this.audioCtx.createGain();
    osc1.type = "sine";
    osc1.frequency.setValueAtTime(587.33, now);
    gain1.gain.setValueAtTime(0, now);
    gain1.gain.linearRampToValueAtTime(0.2, now + 0.05);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
    osc1.connect(gain1);
    gain1.connect(this.audioCtx.destination);
    osc1.start(now);
    osc1.stop(now + 0.5);

    // Chime tone 2: 880 Hz (A5)
    const osc2 = this.audioCtx.createOscillator();
    const gain2 = this.audioCtx.createGain();
    osc2.type = "sine";
    osc2.frequency.setValueAtTime(880, now + 0.35);
    gain2.gain.setValueAtTime(0, now + 0.35);
    gain2.gain.linearRampToValueAtTime(0.25, now + 0.4);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.95);
    osc2.connect(gain2);
    gain2.connect(this.audioCtx.destination);
    osc2.start(now + 0.35);
    osc2.stop(now + 1.0);

    if (callback) {
      setTimeout(callback, 900);
    }
  }

  speakAlert(text) {
    if (!this.speechSynthesis) return;
    try {
      this.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      this.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn("Speech synthesis unavailable:", e);
    }
  }
}

const audioEngine = new AlarmAudioEngine();

function updateSirenUI(isActive) {
  state.sirenActive = isActive;
  const btn = document.getElementById("sirenToggleBtn");
  if (btn) {
    if (isActive) {
      btn.classList.add("active");
      btn.innerHTML = `<span>🔊</span> Siren MUTE`;
    } else {
      btn.classList.remove("active");
      btn.innerHTML = `<span>🔇</span> NFPA 72 Siren`;
    }
  }
}

// ==========================================
// 2. Real-Time Server-Sent Events (SSE)
// ==========================================
function initSSE() {
  const eventSource = new EventSource("/api/stream");

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleServerUpdate(data);
    } catch (err) {
      console.error("Failed to parse SSE payload", err);
    }
  };

  eventSource.onerror = (err) => {
    console.warn("SSE connection interrupted. Retrying via polling fallback...", err);
    // Fallback polling
    setTimeout(fetchStatusFallback, 2500);
  };
}

function fetchStatusFallback() {
  fetch("/api/status")
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        handleServerUpdate(resp.data);
      }
    })
    .catch((err) => console.error("Status fallback error", err));
}

function handleServerUpdate(data) {
  state.scenario = data.scenario;
  state.threat = data.threat;
  state.sensors = data.sensors;
  state.occupants = data.occupant_status;
  state.cameras = data.cameras;
  state.floorplan = data.floorplan;
  state.history = data.history || [];

  renderDashboard();
  renderFloorplanCanvas();
  renderCCTVFeeds();
  renderSensorTelemetry();
  renderSensorChart();
  renderIncidentCommander();

  // Handle emergency voice dispatch on new alarm
  if (state.threat.severity === "CRITICAL" && audioEngine.lastSpokenScenario !== state.scenario) {
    audioEngine.lastSpokenScenario = state.scenario;
    const roomName = data.threat.tactical?.search_priority?.split(",")[0] || "Hazard Zone";
    audioEngine.speakAlert(`Warning. Fire emergency detected in ${roomName}. Evacuation routing active.`);
    if (!audioEngine.isPlaying) {
      audioEngine.startAlarm();
    }
  } else if (state.threat.severity === "NORMAL") {
    audioEngine.lastSpokenScenario = null;
    if (audioEngine.isPlaying) {
      audioEngine.stopAlarm();
    }
  }
}

// ==========================================
// 3. UI Dashboard Rendering & State Updates
// ==========================================
function renderDashboard() {
  const threatBadge = document.getElementById("threatBadge");
  const emergencyBanner = document.getElementById("emergencyBanner");
  const emergencyBannerText = document.getElementById("emergencyBannerText");

  // Threat badge in navbar
  if (threatBadge) {
    if (state.threat.severity === "CRITICAL") {
      threatBadge.className = "threat-status-badge critical";
      threatBadge.innerHTML = `<span class="pulse-dot danger"></span> DEFCON 1 - CRITICAL FIRE ALARM`;
    } else if (state.threat.severity === "HIGH") {
      threatBadge.className = "threat-status-badge critical";
      threatBadge.innerHTML = `<span class="pulse-dot danger"></span> DEFCON 2 - HIGH HAZARD WARNING`;
    } else if (state.threat.severity === "ELEVATED") {
      threatBadge.className = "threat-status-badge";
      threatBadge.style.color = "#fbbf24";
      threatBadge.innerHTML = `<span class="pulse-dot" style="background:#f59e0b"></span> DEFCON 3 - ELEVATED RISK`;
    } else {
      threatBadge.className = "threat-status-badge";
      threatBadge.style.color = "#34d399";
      threatBadge.innerHTML = `<span class="pulse-dot"></span> DEFCON 4 - ALL SYSTEMS NORMAL`;
    }
  }

  // Emergency banner
  if (emergencyBanner) {
    if (state.threat.severity === "CRITICAL" || state.threat.severity === "HIGH") {
      emergencyBanner.classList.add("visible");
      emergencyBannerText.textContent = `CRITICAL HAZARD DETECTED: ${state.threat.tactical.fire_class || "Fire Hazard"}. Suppression Agent: ${state.threat.tactical.primary_agent || "Automated"}. Evacuation routing initiated.`;
    } else {
      emergencyBanner.classList.remove("visible");
    }
  }

  // Quick metrics in hub
  const mEvac = document.getElementById("metricEvacuated");
  const mRisk = document.getElementById("metricRiskScore");
  const mTemp = document.getElementById("metricMaxTemp");
  const mSprinkler = document.getElementById("metricSprinkler");

  if (mEvac) mEvac.textContent = `${state.occupants.evacuated} / ${state.occupants.total}`;
  if (mRisk) mRisk.textContent = `${state.threat.risk_score} / 100`;
  if (mTemp) mTemp.textContent = `${state.threat.thermal_index_c.toFixed(1)}°C`;
  if (mSprinkler) {
    const activeSprinkler = Object.values(state.sensors).find((s) => s.sprinkler !== "STANDBY");
    mSprinkler.textContent = activeSprinkler ? activeSprinkler.sprinkler : "STANDBY (122 PSI)";
  }

  // Active scenario buttons
  document.querySelectorAll(".sim-btn").forEach((btn) => {
    const sc = btn.getAttribute("data-scenario");
    btn.classList.toggle("active", sc === state.scenario);
  });
}

// ==========================================
// 4. Interactive 2D Floorplan Canvas Engine
// ==========================================
let flameParticles = [];
let occupantAvatars = [];

function initFloorplanEntities() {
  // Generate occupant dots scattered in rooms
  occupantAvatars = [
    { x: 120, y: 120, room: "server_b", currentWaypointIdx: 0, progress: 0 },
    { x: 180, y: 150, room: "server_b", currentWaypointIdx: 0, progress: 0 },
    { x: 420, y: 120, room: "chem_lab", currentWaypointIdx: 0, progress: 0 },
    { x: 500, y: 140, room: "chem_lab", currentWaypointIdx: 0, progress: 0 },
    { x: 740, y: 120, room: "executive", currentWaypointIdx: 0, progress: 0 },
    { x: 820, y: 140, room: "executive", currentWaypointIdx: 0, progress: 0 },
    { x: 140, y: 440, room: "cafeteria", currentWaypointIdx: 0, progress: 0 },
    { x: 220, y: 470, room: "cafeteria", currentWaypointIdx: 0, progress: 0 },
    { x: 450, y: 420, room: "open_workspace", currentWaypointIdx: 0, progress: 0 },
    { x: 520, y: 460, room: "open_workspace", currentWaypointIdx: 0, progress: 0 },
    { x: 600, y: 430, room: "open_workspace", currentWaypointIdx: 0, progress: 0 },
    { x: 820, y: 440, room: "mechanical", currentWaypointIdx: 0, progress: 0 }
  ];

  // Initialize flame particle pool
  flameParticles = [];
  for (let i = 0; i < 60; i++) {
    flameParticles.push({
      x: 0,
      y: 0,
      vx: (Math.random() - 0.5) * 1.5,
      vy: -Math.random() * 2.5 - 1.0,
      size: Math.random() * 12 + 6,
      life: Math.random() * 30 + 10,
      maxLife: 40,
      color: Math.random() > 0.4 ? "#f97316" : "#ef4444"
    });
  }
}

let pathFlowOffset = 0;

function renderFloorplanCanvas() {
  const canvases = document.querySelectorAll(".floorplan-canvas");
  if (!canvases.length || !state.floorplan) return;

  canvases.forEach((canvas) => {
    // Only render if visible or in active tab
    if (canvas.offsetParent === null && canvases.length > 1) return;
    const ctx = canvas.getContext("2d");

    // Canvas coordinate space 1000 x 600
    const W = canvas.width;
    const H = canvas.height;

    // Clear background
    ctx.fillStyle = "#070b14";
    ctx.fillRect(0, 0, W, H);

    // Draw architectural grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
    ctx.lineWidth = 1;
    for (let x = 0; x < W; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }
    for (let y = 0; y < H; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    }

    // Draw corridors / hallway connections
    ctx.strokeStyle = "rgba(56, 189, 248, 0.15)";
    ctx.lineWidth = 14;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    state.floorplan.edges.forEach(([u, v]) => {
      const p1 = getNodeCoordinates(u);
      const p2 = getNodeCoordinates(v);
      if (p1 && p2) {
        ctx.beginPath();
        ctx.moveTo(p1[0], p1[1]);
        ctx.lineTo(p2[0], p2[1]);
        ctx.stroke();
      }
    });

    // Draw Rooms
    Object.entries(state.floorplan.rooms).forEach(([roomId, room]) => {
      const isHazard = state.floorplan.blocked_nodes.includes(roomId);
      const isSelected = state.selectedRoom === roomId;

      // Room fill
      if (isHazard) {
        ctx.fillStyle = "rgba(239, 68, 68, 0.22)";
        ctx.strokeStyle = "#ef4444";
        ctx.lineWidth = 2.5;
      } else {
        ctx.fillStyle = isSelected ? "rgba(56, 189, 248, 0.12)" : "rgba(30, 41, 59, 0.55)";
        ctx.strokeStyle = isSelected ? "#38bdf8" : "rgba(255, 255, 255, 0.12)";
        ctx.lineWidth = 1.5;
      }

      ctx.beginPath();
      ctx.roundRect(room.x, room.y, room.w, room.h, 8);
      ctx.fill();
      ctx.stroke();

      // Room Label
      ctx.fillStyle = isHazard ? "#fca5a5" : "#e2e8f0";
      ctx.font = "bold 13px sans-serif";
      ctx.fillText(room.name, room.x + 14, room.y + 26);

      // Hazard type label
      ctx.fillStyle = isHazard ? "#ef4444" : "#64748b";
      ctx.font = "11px monospace";
      ctx.fillText(room.hazard_type, room.x + 14, room.y + 44);

      // Live Room Sensor Badge inside the room
      const sensor = state.sensors[roomId];
      if (sensor) {
        const badgeText = `${sensor.temp.toFixed(1)}°C | Smoke: ${sensor.smoke.toFixed(1)}% | CO: ${sensor.co.toFixed(1)}ppm`;
        ctx.fillStyle = isHazard ? "rgba(239, 68, 68, 0.4)" : "rgba(15, 23, 42, 0.8)";
        ctx.beginPath();
        ctx.roundRect(room.x + 14, room.y + room.h - 32, room.w - 28, 22, 4);
        ctx.fill();

        ctx.fillStyle = isHazard ? "#fee2e2" : "#38bdf8";
        ctx.font = "10px monospace";
        ctx.fillText(badgeText, room.x + 20, room.y + room.h - 17);
      }
    });

    // Draw Emergency Exits with bright glowing emerald icons
    Object.entries(state.floorplan.exits).forEach(([exitId, exit]) => {
      const [ex, ey] = exit.pos;
      ctx.save();
      ctx.shadowColor = "#10b981";
      ctx.shadowBlur = 15;
      ctx.fillStyle = "#10b981";
      ctx.beginPath();
      ctx.roundRect(ex - 28, ey - 14, 56, 28, 6);
      ctx.fill();
      ctx.restore();

      ctx.fillStyle = "#000000";
      ctx.font = "bold 11px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("EXIT", ex, ey);
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";

      ctx.fillStyle = "#34d399";
      ctx.font = "10px sans-serif";
      ctx.fillText(exit.name, ex - 40, ey + 26);
    });

    // Draw Blocked corridor indicators if hazard exists
    state.floorplan.blocked_nodes.forEach((nodeId) => {
      if (nodeId.startsWith("node_")) {
        const pos = getNodeCoordinates(nodeId);
        if (pos) {
          ctx.fillStyle = "rgba(239, 68, 68, 0.9)";
          ctx.beginPath();
          ctx.arc(pos[0], pos[1], 16, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = "#ffffff";
          ctx.font = "bold 16px sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText("✕", pos[0], pos[1]);
          ctx.textAlign = "left";
          ctx.textBaseline = "alphabetic";
        }
      }
    });

    // Draw Dynamic Evacuation Paths (Dijkstra Routes)
    pathFlowOffset = (pathFlowOffset + 1.2) % 30;

    if (state.floorplan.evacuation_routes) {
      Object.entries(state.floorplan.evacuation_routes).forEach(([roomId, route]) => {
        // Highlight paths from occupied/selected rooms
        const isSelected = state.selectedRoom === roomId || state.threat.severity !== "NORMAL";
        if (!isSelected && roomId !== "open_workspace") return;

        const wps = route.waypoints;
        if (!wps || wps.length < 2) return;

        ctx.save();
        ctx.strokeStyle = route.safe ? "#10b981" : "#ef4444";
        ctx.lineWidth = 3.5;
        ctx.setLineDash([10, 8]);
        ctx.lineDashOffset = -pathFlowOffset;
        ctx.shadowColor = route.safe ? "#10b981" : "#ef4444";
        ctx.shadowBlur = 10;

        ctx.beginPath();
        ctx.moveTo(wps[0][0], wps[0][1]);
        for (let i = 1; i < wps.length; i++) {
          ctx.lineTo(wps[i][0], wps[i][1]);
        }
        ctx.stroke();
        ctx.restore();
      });
    }

    // Draw Animated Occupants walking along safe paths
    if (state.threat.severity !== "NORMAL") {
      occupantAvatars.forEach((occ) => {
        const route = state.floorplan.evacuation_routes[occ.room];
        if (route && route.waypoints && route.waypoints.length > 1) {
          occ.progress += 0.008;
          if (occ.progress > 1.0) occ.progress = 1.0;

          const totalSegments = route.waypoints.length - 1;
          const currentSegment = Math.min(totalSegments - 1, Math.floor(occ.progress * totalSegments));
          const segT = (occ.progress * totalSegments) - currentSegment;

          const pA = route.waypoints[currentSegment];
          const pB = route.waypoints[currentSegment + 1];

          const cx = pA[0] + (pB[0] - pA[0]) * segT;
          const cy = pA[1] + (pB[1] - pA[1]) * segT;

          // Draw occupant dot
          ctx.fillStyle = "#38bdf8";
          ctx.shadowColor = "#38bdf8";
          ctx.shadowBlur = 6;
          ctx.beginPath();
          ctx.arc(cx, cy, 5, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      });
    }

    // Draw Animated Flame & Smoke in Hazard Zones
    const hazardRooms = Object.keys(state.floorplan.hazard_zones);
    if (hazardRooms.length > 0) {
      hazardRooms.forEach((hRoomId) => {
        const room = state.floorplan.rooms[hRoomId];
        if (!room) return;
        const originX = room.x + room.w * 0.5;
        const originY = room.y + room.h * 0.55;

        // Draw pulsating thermal core
        const grad = ctx.createRadialGradient(originX, originY, 5, originX, originY, 70);
        grad.addColorStop(0, "rgba(255, 200, 0, 0.85)");
        grad.addColorStop(0.3, "rgba(239, 68, 68, 0.6)");
        grad.addColorStop(0.7, "rgba(185, 28, 28, 0.2)");
        grad.addColorStop(1, "transparent");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(originX, originY, 80, 0, Math.PI * 2);
        ctx.fill();

        // Flame particles
        flameParticles.forEach((p) => {
          p.life--;
          p.x += p.vx;
          p.y += p.vy;
          p.size *= 0.96;

          if (p.life <= 0) {
            p.x = originX + (Math.random() - 0.5) * 40;
            p.y = originY + (Math.random() - 0.5) * 20;
            p.vx = (Math.random() - 0.5) * 1.8;
            p.vy = -Math.random() * 2.8 - 0.8;
            p.size = Math.random() * 12 + 6;
            p.life = Math.random() * 30 + 10;
          }

          ctx.fillStyle = p.color;
          ctx.beginPath();
          ctx.arc(p.x, p.y, Math.max(1, p.size), 0, Math.PI * 2);
          ctx.fill();
        });
      });
    }
  });
}

function getNodeCoordinates(nodeId) {
  if (!state.floorplan) return [500, 300];
  if (state.floorplan.waypoints[nodeId]) {
    return state.floorplan.waypoints[nodeId];
  }
  if (state.floorplan.rooms[nodeId]) {
    return state.floorplan.rooms[nodeId].exit_point;
  }
  if (state.floorplan.exits[nodeId]) {
    return state.floorplan.exits[nodeId].pos;
  }
  return [500, 300];
}

// Continuous requestAnimationFrame loop for smooth canvas animation
function startCanvasAnimationLoop() {
  function loop() {
    renderFloorplanCanvas();
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
}

// Click listener to select rooms or inspect on floorplan
function setupFloorplanInteractivity() {
  const canvases = document.querySelectorAll(".floorplan-canvas");
  if (!canvases.length) return;

  canvases.forEach((canvas) => {
    canvas.addEventListener("click", (e) => {
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const clickX = (e.clientX - rect.left) * scaleX;
      const clickY = (e.clientY - rect.top) * scaleY;

      if (!state.floorplan) return;
      for (const [roomId, room] of Object.entries(state.floorplan.rooms)) {
        if (
          clickX >= room.x &&
          clickX <= room.x + room.w &&
          clickY >= room.y &&
          clickY <= room.y + room.h
        ) {
          state.selectedRoom = roomId;
          highlightRoomInfo(roomId);
          break;
        }
      }
    });
  });
}

function highlightRoomInfo(roomId) {
  const room = state.floorplan?.rooms[roomId];
  const sensor = state.sensors[roomId];
  if (!room || !sensor) return;

  const infoEl = document.getElementById("selectedRoomInfo");
  if (infoEl) {
    infoEl.innerHTML = `
      <div style="font-weight:700; color:#38bdf8; margin-bottom:4px;">${room.name}</div>
      <div style="font-size:0.75rem; color:#94a3b8; font-family:monospace;">
        Hazard: ${room.hazard_type} | Temp: ${sensor.temp.toFixed(1)}°C | Smoke: ${sensor.smoke.toFixed(1)}% | Sprinkler: ${sensor.sprinkler}
      </div>
    `;
  }
}

// ==========================================
// 5. Vision AI Sentinel (CCTV Feeds & WebCam)
// ==========================================
function renderCCTVFeeds() {
  const cams = [
    { id: "cam_server", canvasId: "cctvCanvasServer", label: "CAM 01 - SERVER B" },
    { id: "cam_cafe", canvasId: "cctvCanvasCafe", label: "CAM 02 - CAFETERIA" },
    { id: "cam_lab", canvasId: "cctvCanvasLab", label: "CAM 03 - CHEM LAB 4" },
    { id: "cam_lobby", canvasId: "cctvCanvasLobby", label: "CAM 04 - RECEPTION" }
  ];

  cams.forEach((c) => {
    const canvas = document.getElementById(c.canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const camData = state.cameras[c.id];
    const isFire = camData && camData.flame_detected;

    const W = canvas.width;
    const H = canvas.height;

    // Room background simulation
    ctx.fillStyle = isFire ? "#240d0d" : "#080e1a";
    ctx.fillRect(0, 0, W, H);

    // Draw simulated room perspective lines
    ctx.strokeStyle = isFire ? "rgba(239, 68, 68, 0.2)" : "rgba(56, 189, 248, 0.1)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, H * 0.75);
    ctx.lineTo(W, H * 0.75);
    ctx.moveTo(0, H);
    ctx.lineTo(W * 0.35, H * 0.75);
    ctx.moveTo(W, H);
    ctx.lineTo(W * 0.65, H * 0.75);
    ctx.stroke();

    if (isFire) {
      // Draw simulated flickering flame inside camera
      const fx = W * 0.45;
      const fy = H * 0.55;
      const fRad = 35 + Math.sin(Date.now() * 0.015) * 8;

      const fGrad = ctx.createRadialGradient(fx, fy, 4, fx, fy, fRad);
      fGrad.addColorStop(0, "#fef08a");
      fGrad.addColorStop(0.3, "#f97316");
      fGrad.addColorStop(0.7, "#ef4444");
      fGrad.addColorStop(1, "transparent");
      ctx.fillStyle = fGrad;
      ctx.beginPath();
      ctx.arc(fx, fy, fRad, 0, Math.PI * 2);
      ctx.fill();

      // Draw AI Bounding Boxes
      camData.bounding_boxes.forEach((box) => {
        const bx = (box.x_pct / 100) * W;
        const by = (box.y_pct / 100) * H;
        const bw = (box.w_pct / 100) * W;
        const bh = (box.h_pct / 100) * H;

        ctx.strokeStyle = box.color || "#ef4444";
        ctx.lineWidth = 2;
        ctx.strokeRect(bx, by, bw, bh);

        // Box label tag
        ctx.fillStyle = box.color || "#ef4444";
        ctx.fillRect(bx, by - 18, bw, 18);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 9px monospace";
        ctx.fillText(`${box.label} [${Math.round(box.confidence * 100)}%]`, bx + 4, by - 5);
      });
    }

    // Camera Scanline & Timestamp HUD
    ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
    ctx.font = "10px monospace";
    ctx.fillText(`${c.label} | ${new Date().toLocaleTimeString()} | 30 FPS`, 10, H - 10);
  });
}

// Live User WebCam Integration with Client-Side Fire & Heat Detection
async function toggleWebcam() {
  const btn = document.getElementById("toggleWebcamBtn");
  const video = document.getElementById("webcamVideo");
  const overlay = document.getElementById("webcamOverlayCanvas");
  const webcamStatus = document.getElementById("webcamStatusText");

  if (state.webcamActive) {
    // Stop webcam
    if (state.webcamStream) {
      state.webcamStream.getTracks().forEach((track) => track.stop());
      state.webcamStream = null;
    }
    state.webcamActive = false;
    video.srcObject = null;
    btn.innerHTML = `<span>📹</span> Connect Live WebCam`;
    btn.classList.remove("btn-danger");
    btn.classList.add("btn-primary");
    webcamStatus.textContent = "WebCam disconnected. Click button to test real-time vision AI.";
  } else {
    // Request webcam access
    try {
      webcamStatus.textContent = "Requesting browser camera permission...";
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 360 } },
        audio: false
      });
      state.webcamStream = stream;
      video.srcObject = stream;
      state.webcamActive = true;
      btn.innerHTML = `<span>🛑</span> Disconnect WebCam`;
      btn.classList.remove("btn-primary");
      btn.classList.add("btn-danger");
      webcamStatus.textContent = "AI Sentinel Vision ACTIVE: Analyzing video stream for flame/smoke signatures...";

      startWebcamAnalysisLoop();
    } catch (err) {
      console.error("Webcam access denied or error:", err);
      webcamStatus.textContent = `Camera error: ${err.message}. Ensure camera permissions are granted.`;
    }
  }
}

function startWebcamAnalysisLoop() {
  const video = document.getElementById("webcamVideo");
  const overlay = document.getElementById("webcamOverlayCanvas");
  if (!overlay || !video) return;
  const ctx = overlay.getContext("2d");

  // Hidden analysis buffer canvas
  const buff = document.createElement("canvas");
  buff.width = 160;
  buff.height = 90;
  const bCtx = buff.getContext("2d");

  function processFrame() {
    if (!state.webcamActive || video.paused || video.ended) return;

    overlay.width = video.videoWidth || 640;
    overlay.height = video.videoHeight || 360;
    ctx.clearRect(0, 0, overlay.width, overlay.height);

    // Draw frame to low-res buffer for fast pixel analysis
    bCtx.drawImage(video, 0, 0, buff.width, buff.height);
    const imgData = bCtx.getImageData(0, 0, buff.width, buff.height);
    const d = imgData.data;

    let firePixels = 0;
    let minX = buff.width, maxX = 0, minY = buff.height, maxY = 0;

    // Heuristic color analysis for flame: High Red (R > 180), high Green (G > 100), low Blue (B < 80)
    for (let i = 0; i < d.length; i += 4) {
      const r = d[i];
      const g = d[i + 1];
      const b = d[i + 2];
      const px = (i / 4) % buff.width;
      const py = Math.floor((i / 4) / buff.width);

      if (r > 175 && g > 90 && b < 100 && (r - g) > 20 && (r - b) > 75) {
        firePixels++;
        if (px < minX) minX = px;
        if (px > maxX) maxX = px;
        if (py < minY) minY = py;
        if (py > maxY) maxY = py;
      }
    }

    const fireRatio = firePixels / (buff.width * buff.height);
    const scaleX = overlay.width / buff.width;
    const scaleY = overlay.height / buff.height;

    // If significant flame color cluster detected
    if (firePixels > 25 && fireRatio > 0.003) {
      const bx = minX * scaleX;
      const by = minY * scaleY;
      const bw = (maxX - minX) * scaleX;
      const bh = (maxY - minY) * scaleY;

      // Draw AI Detection Bounding Box on live user video!
      ctx.strokeStyle = "#ef4444";
      ctx.lineWidth = 3;
      ctx.strokeRect(bx, by, bw, bh);

      ctx.fillStyle = "#ef4444";
      ctx.fillRect(bx, by - 22, bw, 22);
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 11px monospace";
      ctx.fillText(`FLAME HAZARD DETECTED [${Math.min(99, Math.round(fireRatio * 3000))}%]`, bx + 6, by - 6);

      const statusText = document.getElementById("webcamStatusText");
      if (statusText) {
        statusText.innerHTML = `<span style="color:#ef4444; font-weight:700;">⚠️ REAL-TIME FLAME SIGNATURE DETECTED BY WEBCAM SENTINEL!</span>`;
      }
    } else {
      const statusText = document.getElementById("webcamStatusText");
      if (statusText && state.webcamActive) {
        statusText.innerHTML = `<span style="color:#10b981;">AI Vision Active: Normal ambient conditions. Hold up a flame/lighter/red card to test!</span>`;
      }
    }

    requestAnimationFrame(processFrame);
  }

  video.addEventListener("play", () => {
    requestAnimationFrame(processFrame);
  });
}

// ==========================================
// 6. Sensor Telemetry Grid & Chart
// ==========================================
function renderSensorTelemetry() {
  const container = document.getElementById("sensorTelemetryGrid");
  if (!container || !state.sensors) return;

  container.innerHTML = Object.entries(state.sensors)
    .map(([roomId, s]) => {
      const isAlarm = s.status !== "NORMAL";
      return `
      <div class="sensor-box ${isAlarm ? "alarm" : ""}">
        <div class="sensor-box-title">
          <span>${s.name}</span>
          <span class="status-pill ${isAlarm ? "violation" : "compliant"}">${s.status}</span>
        </div>
        <div class="sensor-data-grid">
          <div class="data-pair">
            <span>Temperature</span>
            <span style="color:${s.temp > 35 ? "#ef4444" : "#e2e8f0"}">${s.temp.toFixed(1)} °C</span>
          </div>
          <div class="data-pair">
            <span>Smoke Obscuration</span>
            <span style="color:${s.smoke > 10 ? "#ef4444" : "#e2e8f0"}">${s.smoke.toFixed(1)} %/ft</span>
          </div>
          <div class="data-pair">
            <span>Carbon Monoxide</span>
            <span style="color:${s.co > 25 ? "#ef4444" : "#e2e8f0"}">${s.co.toFixed(1)} ppm</span>
          </div>
          <div class="data-pair">
            <span>Volatile Gas</span>
            <span>${s.voc} ppb</span>
          </div>
          <div class="data-pair">
            <span>Sprinkler State</span>
            <span>${s.sprinkler}</span>
          </div>
          <div class="data-pair">
            <span>HVAC Airflow</span>
            <span>${s.hvac_cfm} CFM</span>
          </div>
        </div>
      </div>
    `;
    })
    .join("");
}

// Custom High-Performance Canvas Sensor Chart
function renderSensorChart() {
  const canvas = document.getElementById("sensorTrendChart");
  if (!canvas || !state.history || state.history.length === 0) return;
  const ctx = canvas.getContext("2d");

  const W = canvas.width;
  const H = canvas.height;

  ctx.clearRect(0, 0, W, H);

  // Background grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  for (let y = 20; y < H; y += 30) {
    ctx.beginPath();
    ctx.moveTo(40, y);
    ctx.lineTo(W - 10, y);
    ctx.stroke();
  }

  const data = state.history;
  const N = data.length;
  if (N < 2) return;

  const stepX = (W - 60) / (N - 1);
  const maxVal = Math.max(100, ...data.map((d) => Math.max(d.max_temp, d.max_smoke, d.max_co)));

  function drawSeries(key, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.beginPath();

    data.forEach((pt, i) => {
      const x = 50 + i * stepX;
      const y = H - 25 - (pt[key] / maxVal) * (H - 45);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.stroke();

    // End point dot
    const lastX = 50 + (N - 1) * stepX;
    const lastY = H - 25 - (data[N - 1][key] / maxVal) * (H - 45);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  // Draw curves: Temp (Red), Smoke (Orange), CO (Cyan)
  drawSeries("max_temp", "#ef4444");
  drawSeries("max_smoke", "#f97316");
  drawSeries("max_co", "#06b6d4");

  // Chart Y-Axis legend
  ctx.fillStyle = "#64748b";
  ctx.font = "9px monospace";
  ctx.fillText(`${Math.round(maxVal)}`, 8, 25);
  ctx.fillText("0", 25, H - 25);
}

// ==========================================
// 7. Incident Commander & 911 Dispatch Hub
// ==========================================
function renderIncidentCommander() {
  const cadBox = document.getElementById("cadDispatchText");
  const tacticalBox = document.getElementById("tacticalResponseGuide");

  const t = state.threat.tactical || {};
  const cad = t.dispatch_cad || {};

  if (cadBox) {
    cadBox.textContent = `
[911 EMERGENCY COMPUTER-AIDED DISPATCH (CAD) TRANSMISSION]
--------------------------------------------------------------------------------
BOX ALARM CODE    : ${cad.box_code || "STANDBY"}
FACILITY ADDRESS  : ${cad.facility || "Apex BioTech Research Facility, Bldg 4"}
GPS COORDINATES   : ${cad.lat_lon || "37.7749° N, 122.4194° W"}
NEAREST HYDRANT   : ${cad.nearest_hydrant || "Hydrant #12"}
ASSIGNED UNITS    : ${(cad.recommended_units || []).join(", ") || "Standby"}

TACTICAL SITREP   :
${cad.tactical_radio_note || "All zones nominal."}

OCCUPANCY COUNT   : ${state.occupants.total} Total | ${state.occupants.evacuated} Evacuated | ${state.occupants.in_transit} In Transit
AUTOMATED SYSTEM  : Nexus Fire Safety AI Engine v3.4 [NFPA 72 & 101 Certified]
--------------------------------------------------------------------------------
    `.trim();
  }

  if (tacticalBox) {
    tacticalBox.innerHTML = `
      <div style="margin-bottom:12px;">
        <span style="color:#64748b; font-size:0.75rem; text-transform:uppercase;">Class of Fire:</span>
        <div style="font-size:1.05rem; font-weight:700; color:#f87171;">${t.fire_class || "Class A Normal"}</div>
      </div>
      <div style="margin-bottom:12px;">
        <span style="color:#64748b; font-size:0.75rem; text-transform:uppercase;">Mandated Suppression Agent:</span>
        <div style="font-weight:600; color:#38bdf8;">${t.primary_agent || "Standard Wet Sprinkler"}</div>
      </div>
      <div style="margin-bottom:12px;">
        <span style="color:#64748b; font-size:0.75rem; text-transform:uppercase;">PROHIBITED AGENTS:</span>
        <div style="font-weight:600; color:#ef4444;">${t.avoid_agent || "None"}</div>
      </div>
      <div style="margin-bottom:12px;">
        <span style="color:#64748b; font-size:0.75rem; text-transform:uppercase;">HVAC Ventilation Protocol:</span>
        <div style="color:#cbd5e1; font-size:0.82rem;">${t.ventilation || "Standard cycle"}</div>
      </div>
      <div>
        <span style="color:#64748b; font-size:0.75rem; text-transform:uppercase;">Identified Facility Hazards:</span>
        <div style="color:#cbd5e1; font-size:0.82rem;">${t.hazards || "None"}</div>
      </div>
    `;
  }
}

function copyCADDispatch() {
  const cadText = document.getElementById("cadDispatchText")?.textContent;
  if (cadText) {
    navigator.clipboard.writeText(cadText).then(() => {
      alert("911 CAD Dispatch Payload copied to clipboard!");
    });
  }
}

// ==========================================
// 8. Life Safety & NFPA Compliance Audits
// ==========================================
function loadComplianceData() {
  fetch("/api/compliance")
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        renderComplianceView(resp.data);
      }
    })
    .catch((err) => console.error("Compliance fetch error", err));
}

function renderComplianceView(compData) {
  const scoreEl = document.getElementById("complianceScoreVal");
  const gradeEl = document.getElementById("complianceGradeVal");
  const tbody = document.getElementById("complianceTableBody");

  if (scoreEl) scoreEl.textContent = `${compData.score}%`;
  if (gradeEl) gradeEl.textContent = `Grade ${compData.grade}`;

  if (tbody && compData.items) {
    tbody.innerHTML = compData.items
      .map((item) => {
        const statusClass = item.status.toLowerCase();
        return `
        <tr>
          <td style="font-family:monospace; font-weight:700;">${item.code}</td>
          <td><span style="color:#38bdf8; font-weight:600;">${item.standard}</span> - ${item.category}</td>
          <td>
            <strong>${item.title}</strong>
            <div style="color:#94a3b8; font-size:0.72rem; margin-top:2px;">${item.requirement}</div>
          </td>
          <td>
            <select class="sim-btn" onchange="toggleComplianceItem(${item.id}, this.value)">
              <option value="COMPLIANT" ${item.status === "COMPLIANT" ? "selected" : ""}>COMPLIANT</option>
              <option value="WARNING" ${item.status === "WARNING" ? "selected" : ""}>WARNING</option>
              <option value="VIOLATION" ${item.status === "VIOLATION" ? "selected" : ""}>VIOLATION</option>
            </select>
          </td>
          <td style="font-size:0.74rem; color:#94a3b8;">${item.last_inspected}</td>
          <td style="font-size:0.74rem;">${item.remediation || "N/A"}</td>
        </tr>
      `;
      })
      .join("");
  }
}

function toggleComplianceItem(itemId, newStatus) {
  fetch("/api/compliance/toggle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: itemId, status: newStatus })
  })
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        loadComplianceData();
      }
    })
    .catch((err) => console.error("Compliance toggle error", err));
}

// ==========================================
// 9. Incident Log History
// ==========================================
function loadIncidentHistory() {
  fetch("/api/incidents")
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        renderIncidentList(resp.data);
      }
    })
    .catch((err) => console.error("Incidents fetch error", err));
}

function renderIncidentList(incidents) {
  const container = document.getElementById("incidentLogContainer");
  if (!container) return;

  container.innerHTML = incidents
    .map((inc) => {
      return `
      <div style="padding:12px; border-bottom:1px solid rgba(255,255,255,0.06); font-size:0.8rem;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <span style="font-family:monospace; color:#38bdf8; font-weight:700;">${inc.incident_code}</span>
          <span class="status-pill ${inc.severity === "HIGH" ? "warning" : inc.severity === "CRITICAL" ? "violation" : "compliant"}">${inc.severity}</span>
        </div>
        <div style="font-weight:600; color:#f1f5f9;">${inc.title} - ${inc.location}</div>
        <div style="color:#94a3b8; font-size:0.74rem; margin-top:2px;">${inc.ai_summary}</div>
        <div style="color:#64748b; font-size:0.7rem; margin-top:4px; font-family:monospace;">${inc.created_at} | Suppressed via ${inc.suppression_medium}</div>
      </div>
    `;
    })
    .join("");
}

// ==========================================
// 10. Scenario Controls & Tab Management
// ==========================================
function triggerScenario(scenarioName) {
  fetch("/api/simulation/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario: scenarioName })
  })
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        handleServerUpdate(resp.data);
      }
    })
    .catch((err) => console.error("Trigger scenario error", err));
}

function resetScenario() {
  fetch("/api/simulation/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  })
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        handleServerUpdate(resp.data);
      }
    })
    .catch((err) => console.error("Reset scenario error", err));
}

function switchTab(tabId) {
  state.currentTab = tabId;
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });
  document.querySelectorAll(".tab-view").forEach((view) => {
    view.classList.toggle("active", view.id === `tabView_${tabId}`);
  });

  if (tabId === "compliance") {
    loadComplianceData();
  } else if (tabId === "incidents") {
    loadIncidentHistory();
  }
}

function toggleModal(modalId, show) {
  const el = document.getElementById(modalId);
  if (el) {
    el.classList.toggle("active", show);
  }
}

// ==========================================
// 11. What-If Sandbox Room Hazard Injection
// ==========================================
function injectSelectedRoomHazard(temp = 84, smoke = 45, flame = true) {
  const roomId = state.selectedRoom || "server_b";
  fetch("/api/simulation/hazard", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ room_id: roomId, temp, smoke, flame })
  })
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        handleServerUpdate(resp.data);
      }
    })
    .catch((err) => console.error("Hazard injection error", err));
}

function clearSelectedRoomHazard() {
  const roomId = state.selectedRoom || "server_b";
  fetch("/api/simulation/hazard/clear", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ room_id: roomId })
  })
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success) {
        handleServerUpdate(resp.data);
      }
    })
    .catch((err) => console.error("Hazard clear error", err));
}

// ==========================================
// 12. Nexus AI Fire Safety Co-Pilot Chat
// ==========================================
function toggleAiDrawer(show) {
  const drawer = document.getElementById("aiDrawer");
  const overlay = document.getElementById("aiDrawerOverlay");
  if (drawer && overlay) {
    drawer.classList.toggle("active", show);
    overlay.classList.toggle("active", show);
    if (show) {
      const historyEl = document.getElementById("aiChatHistory");
      if (historyEl && historyEl.children.length === 0) {
        appendAiMessage("bot", `### 👋 Greetings, Commander. I am Nexus AI.
I am monitoring **28 calibrated IoT telemetry nodes** across Apex BioTech Building 4.

You can ask me about:
- **Fire suppression agent matching** (Lithium, Solvents, Grease)
- **Dynamic Dijkstra egress route validation**
- **NFPA 10, 72 & 101 compliance standards**
- **Drafting emergency public address (PA) scripts**
- Or click any recommendation chip above!`);
      }
      setTimeout(() => {
        document.getElementById("aiChatInput")?.focus();
      }, 200);
    }
  }
}

function askAiPreset(queryText) {
  const input = document.getElementById("aiChatInput");
  if (input) {
    input.value = queryText;
    sendAiQuery(queryText);
  }
}

function handleAiChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("aiChatInput");
  const query = input?.value?.trim();
  if (!query) return;
  input.value = "";
  sendAiQuery(query);
}

function sendAiQuery(queryText) {
  appendAiMessage("user", queryText);

  // Show typing indicator
  const historyEl = document.getElementById("aiChatHistory");
  const typingId = "aiTypingIndicator";
  const typingEl = document.createElement("div");
  typingEl.id = typingId;
  typingEl.className = "ai-msg bot";
  typingEl.innerHTML = `<div class="ai-msg-bubble"><span class="pulse-dot"></span> <em>Nexus AI analyzing telemetry & NFPA standards...</em></div>`;
  historyEl?.appendChild(typingEl);
  historyEl?.scrollTo({ top: historyEl.scrollHeight, behavior: "smooth" });

  fetch("/api/ai/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: queryText })
  })
    .then((r) => r.json())
    .then((resp) => {
      document.getElementById(typingId)?.remove();
      if (resp.success && resp.data) {
        appendAiMessage("bot", resp.data.reply, resp.data);
      } else {
        appendAiMessage("bot", "⚠️ Unable to query AI engine. Please verify server connection.");
      }
    })
    .catch((err) => {
      document.getElementById(typingId)?.remove();
      console.error("AI chat error", err);
      appendAiMessage("bot", `⚠️ Error communicating with AI incident engine: ${err.message}`);
    });
}

function formatMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/^### (.*$)/gim, "<h3>$1</h3>")
    .replace(/^## (.*$)/gim, "<h2>$1</h2>")
    .replace(/^# (.*$)/gim, "<h1>$1</h1>")
    .replace(/^\> (.*$)/gim, "<blockquote>$1</blockquote>")
    .replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/gim, "<em>$1</em>")
    .replace(/`([^`]+)`/gim, "<code style='background:rgba(0,0,0,0.4); padding:2px 5px; border-radius:4px; font-family:monospace;'>$1</code>")
    .replace(/^\- (.*$)/gim, "<li>$1</li>")
    .replace(/\n\n/gim, "<br><br>");
  return html;
}

function appendAiMessage(role, text, data = null) {
  const historyEl = document.getElementById("aiChatHistory");
  if (!historyEl) return;

  const msgDiv = document.createElement("div");
  msgDiv.className = `ai-msg ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "ai-msg-bubble";
  bubble.innerHTML = formatMarkdown(text);
  msgDiv.appendChild(bubble);

  // If bot response has suggestions or audio speech
  if (role === "bot" && data) {
    const actionsDiv = document.createElement("div");
    actionsDiv.className = "ai-msg-actions";

    if (data.spoken_summary) {
      const speakBtn = document.createElement("button");
      speakBtn.className = "ai-speak-btn";
      speakBtn.innerHTML = `<span>🔊</span> Listen`;
      speakBtn.onclick = () => audioEngine.speakAlert(data.spoken_summary);
      actionsDiv.appendChild(speakBtn);
    }

    if (data.suggested_actions && data.suggested_actions.length > 0) {
      data.suggested_actions.forEach((act) => {
        const actBtn = document.createElement("button");
        actBtn.className = "ai-action-btn";
        actBtn.textContent = act;
        actBtn.onclick = () => {
          if (act.includes("Floorplan")) switchTab("floorplan");
          else if (act.includes("Compliance")) switchTab("compliance");
          else if (act.includes("CAD") || act.includes("Engine")) switchTab("dispatch");
          else if (act.includes("WebCam")) switchTab("vision");
          else askAiPreset(act);
        };
        actionsDiv.appendChild(actBtn);
      });
    }

    if (actionsDiv.children.length > 0) {
      msgDiv.appendChild(actionsDiv);
    }
  }

  historyEl.appendChild(msgDiv);
  historyEl.scrollTo({ top: historyEl.scrollHeight, behavior: "smooth" });
}

// ==========================================
// 13. Interactive Fire Commander Drill
// ==========================================
function openDrillModal() {
  const resultBox = document.getElementById("drillResultBox");
  if (resultBox) resultBox.style.display = "none";
  toggleModal("drillModal", true);
}

function submitDrillDecisions() {
  const suppression = document.getElementById("drillSuppressionSelect")?.value || "fm200";
  const hvac = document.getElementById("drillHvacSelect")?.value || "seal_recirc";
  const egress = document.getElementById("drillEgressSelect")?.value || "east_stairwell";

  const btn = document.getElementById("drillSubmitBtn");
  if (btn) btn.textContent = "Evaluating Tactical Decisions...";

  fetch("/api/drill/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scenario: "electrical_server",
      suppression,
      hvac,
      egress
    })
  })
    .then((r) => r.json())
    .then((resp) => {
      if (btn) btn.textContent = "Submit Command Decisions ➔";
      if (resp.success && resp.data) {
        renderDrillResults(resp.data);
      }
    })
    .catch((err) => {
      if (btn) btn.textContent = "Submit Command Decisions ➔";
      alert("Error evaluating drill: " + err.message);
    });
}

function renderDrillResults(res) {
  const box = document.getElementById("drillResultBox");
  if (!box) return;

  const isHigh = res.score >= 80;
  box.style.display = "block";
  box.style.background = isHigh ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)";
  box.style.border = `1px solid ${isHigh ? "#10b981" : "#ef4444"}`;

  box.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
      <div>
        <div style="font-size:1.15rem; font-weight:700; color:${isHigh ? "#34d399" : "#f87171"};">
          Score: ${res.score} / 100
        </div>
        <div style="font-size:0.8rem; color:#38bdf8; font-weight:600;">Rank: ${res.rank}</div>
      </div>
      <div style="font-size:0.72rem; color:#94a3b8; font-family:monospace;">${res.certified_date}</div>
    </div>
    <div style="display:flex; flex-direction:column; gap:6px; font-size:0.78rem;">
      ${res.feedback.map((f) => `<div>${f}</div>`).join("")}
    </div>
  `;
}

// ==========================================
// 14. NFPA 901 Incident Action Plan (IAP)
// ==========================================
function openIapModal() {
  toggleModal("iapModal", true);
  const container = document.getElementById("iapContentBody");
  if (!container) return;
  container.innerHTML = "Generating official NFPA 901 Incident Action Plan...";

  fetch("/api/report/iap")
    .then((r) => r.json())
    .then((resp) => {
      if (resp.success && resp.data) {
        const d = resp.data;
        container.innerHTML = `
================================================================================
          NATIONAL FIRE PROTECTION ASSOCIATION &bull; NFPA 901 INCIDENT ACTION PLAN
                          INCIDENT COMMAND SYSTEM (ICS FORM 202/204)
================================================================================
REPORT ID          : ${d.report_id}
TIMESTAMP          : ${d.timestamp}
OPERATION NAME     : ${d.incident_name}
FACILITY           : ${d.facility}
OPERATIONAL PERIOD : ${d.operational_period}
--------------------------------------------------------------------------------
1. INCIDENT COMMAND STAFF:
   - Incident Commander : ${d.command_staff.incident_commander}
   - Safety Officer     : ${d.command_staff.safety_officer}
   - Operations Chief   : ${d.command_staff.operations_chief}

2. TACTICAL LIFE SAFETY OBJECTIVES:
${d.tactical_objectives.map((o) => `   ${o}`).join("\n")}

3. REAL-TIME HAZARD TELEMETRY LEDGER:
   - Peak Thermal Hotspot    : ${d.hazard_ledger.peak_thermal}
   - Smoke Obscuration       : ${d.hazard_ledger.smoke_obscuration}
   - Carbon Monoxide Density : ${d.hazard_ledger.co_density}
   - Flashover Probability   : ${d.hazard_ledger.flashover_risk}
   - Flame Signature Confirmed: ${d.hazard_ledger.flame_confirmed ? "YES (Vision Sentinel + Thermal)" : "NO (Atmospheric Nominal)"}

4. LOGISTICS & FIRST-RESPONDER RESOURCES:
   - Assigned Units       : ${d.logistics.assigned_units.join(", ")}
   - Nearest Hydrant      : ${d.logistics.hydrant}
   - Tactical Radio Channel: ${d.logistics.radio_tactical_channel}
   - Staging Area         : ${d.logistics.staging_area}
--------------------------------------------------------------------------------
VERIFIED BY: Nexus Autonomous Fire Safety Artificial Intelligence v3.4
SIGNATURE  : [DIGITALLY SIGNED & HASHED VIA SHA-256 SECURE TELEMETRY CHAIN]
================================================================================
        `.trim();
      }
    })
    .catch((err) => {
      container.textContent = "Failed to load IAP: " + err.message;
    });
}

// ==========================================
// 15. Facility PA Voice Broadcast System
// ==========================================
function setPaPreset(type) {
  const input = document.getElementById("paBroadcastInput");
  if (!input) return;
  if (type === "evac") {
    input.value = "Attention building occupants: emergency evacuation in progress. Follow illuminated green egress vectors to the nearest exit.";
  } else if (type === "shelter") {
    input.value = "Warning: hazardous chemical vapor containment in progress. Remain inside your current room and seal doors.";
  } else if (type === "clear") {
    input.value = "All clear. Emergency situation resolved. Normal building operations have resumed.";
  }
}

function broadcastPAAnnouncement() {
  const input = document.getElementById("paBroadcastInput");
  const text = input?.value?.trim();
  if (!text) return;

  // Play realistic two-tone chime first, then voice
  audioEngine.playPAChime(() => {
    audioEngine.speakAlert(text);
  });
}

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initFloorplanEntities();
  setupFloorplanInteractivity();
  startCanvasAnimationLoop();
  initSSE();
  loadComplianceData();
  loadIncidentHistory();

  // Tab click listeners
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      switchTab(tab);
    });
  });

  // Scenario buttons
  document.querySelectorAll(".sim-btn[data-scenario]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sc = btn.getAttribute("data-scenario");
      if (sc === "normal") {
        resetScenario();
      } else {
        triggerScenario(sc);
      }
    });
  });
});
