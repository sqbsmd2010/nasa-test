import * as THREE from "three";
import "./styles.css";

// --- Scene ---------------------------------------------------------------
const canvas = document.getElementById("scene") as HTMLCanvasElement;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x05070d);
const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 5000);
camera.position.set(40, 22, 60);
camera.lookAt(0, 4, 0);

// Harsh, low-angle sun: no atmosphere, hard shadows. Position will come from JPL Horizons.
const sun = new THREE.DirectionalLight(0xfff4e0, 3.2);
sun.position.set(-120, 40, 60);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -80, right: 80, top: 80, bottom: -80, far: 400 });
scene.add(sun, new THREE.AmbientLight(0x1b2230, 0.35));

// Terrain: procedural placeholder. TODO: replace with LOLA DEM heightmap (NASA Trek).
const geo = new THREE.PlaneGeometry(400, 400, 256, 256);
geo.rotateX(-Math.PI / 2);
const pos = geo.attributes.position;
for (let i = 0; i < pos.count; i++) {
  const x = pos.getX(i), z = pos.getZ(i);
  const h = Math.sin(x * 0.04) * Math.cos(z * 0.05) * 3 + Math.sin(x * 0.17 + z * 0.13) * 0.4;
  pos.setY(i, h);
}
geo.computeVertexNormals();
const ground = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0x7d8390, roughness: 0.97 }));
ground.receiveShadow = true;
scene.add(ground);

// Habitat modules (placeholder geometry; swap for Blender GLB assets)
const hab = new THREE.MeshStandardMaterial({ color: 0xd7dce4, metalness: 0.3, roughness: 0.55 });
for (const [x, z] of [[0, 0], [10, 2], [-9, -4]]) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 9, 32).rotateZ(Math.PI / 2), hab);
  m.position.set(x, 3.2, z);
  m.castShadow = true;
  scene.add(m);
}

// Stars
const starPos = new Float32Array(3000 * 3);
for (let i = 0; i < starPos.length; i += 3) {
  const v = new THREE.Vector3().randomDirection().multiplyScalar(2500);
  starPos.set([v.x, Math.abs(v.y), v.z], i);
}
const stars = new THREE.BufferGeometry().setAttribute("position", new THREE.BufferAttribute(starPos, 3));
scene.add(new THREE.Points(stars, new THREE.PointsMaterial({ color: 0xffffff, size: 1.6, sizeAttenuation: false })));

function resize() {
  renderer.setSize(innerWidth, innerHeight, false);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

let t = 0;
renderer.setAnimationLoop(() => {
  t += 0.0015;
  camera.position.x = Math.cos(t) * 70;
  camera.position.z = Math.sin(t) * 70;
  camera.lookAt(0, 4, 0);
  renderer.render(scene, camera);
});

// --- Live telemetry from the Python sim -----------------------------------
const hud = document.getElementById("hud")!;
const labels: Record<string, string> = { sol: "Sol", power_kw: "Power kW", o2_pct: "O2 %", water_l: "Water L", food_kcal: "Food kcal", dose_msv: "Dose mSv", morale: "Morale" };
hud.innerHTML = `<h1>Outpost</h1><div id="rows"></div>`;
const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/sim`);
ws.onmessage = (e) => {
  const tel = JSON.parse(e.data).telemetry as Record<string, number>;
  document.getElementById("rows")!.innerHTML = Object.entries(labels)
    .map(([k, l]) => `<div class="row"><span>${l}</span><span>${tel[k]}</span></div>`).join("");
};
