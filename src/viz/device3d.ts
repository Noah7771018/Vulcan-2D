// ============================================================================
//  Device view - distributed soft-breakdown representation for v0.3.
//
//  The h-BN area is K parallel sub-populations ("patches"). As the breakdown
//  fraction phi_bar rises during SET, patches cross a spread of thresholds and
//  light up progressively across the area. A patch is a coarse-grained local
//  region, not a literal filament geometry; it can represent a defect bridge,
//  a metal-assisted confined path, or a CAFM hotspot.
//
//  Glow uses unlit basic materials + additive halos (no HDR bloom): renders the
//  same warm orange on every GPU (a software-renderer pink artifact bit us once).
// ============================================================================

import {
  Scene,
  PerspectiveCamera,
  WebGLRenderer,
  Mesh,
  CylinderGeometry,
  MeshStandardMaterial,
  MeshBasicMaterial,
  PointLight,
  DirectionalLight,
  HemisphereLight,
  Group,
  Color,
  PMREMGenerator,
  ACESFilmicToneMapping,
  PCFSoftShadowMap,
  PlaneGeometry,
  ShadowMaterial,
  SRGBColorSpace,
  Sprite,
  SpriteMaterial,
  CanvasTexture,
  AdditiveBlending,
  Texture,
} from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { forgeRamp } from './theme';

export interface DeviceGeometry {
  hbnLayers: number;
  topThickness: number;
  bottomThickness: number;
}

interface Patch {
  mesh: Mesh;
  halo: Sprite;
  thr: number; // breakdown threshold in [0,1]
}

const RADIUS = 1.5;
const LAYER_H = 0.16;

export class Device3D {
  readonly renderer: WebGLRenderer;
  private scene = new Scene();
  private camera: PerspectiveCamera;
  private controls: OrbitControls;
  private glowTex: Texture;

  private stack = new Group();
  private patchGroup = new Group();
  private patches: Patch[] = [];
  private hotspot: PointLight;

  private phi = 0;
  private targetPhi = 0;
  private K = 10;
  private geom: DeviceGeometry = { hbnLayers: 6, topThickness: 0.6, bottomThickness: 0.6 };

  constructor(canvas: HTMLCanvasElement) {
    this.renderer = new WebGLRenderer({ canvas, antialias: true });
    this.renderer.setClearColor(0x07080b, 1);
    this.renderer.toneMapping = ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = PCFSoftShadowMap;
    this.renderer.outputColorSpace = SRGBColorSpace;

    const pmrem = new PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.background = makeGradientTexture();
    this.glowTex = makeGlowTexture();

    this.camera = new PerspectiveCamera(40, 1, 0.1, 100);
    this.camera.position.set(4.0, 1.35, 5.0); // side-on so the h-BN interior is visible

    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 3;
    this.controls.maxDistance = 12;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 0.5;

    this.scene.add(new HemisphereLight(0xaab4c4, 0x140d0a, 0.55));
    const key = new DirectionalLight(0xfff0dd, 2.2);
    key.position.set(5, 8, 4);
    key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    key.shadow.camera.near = 1;
    key.shadow.camera.far = 30;
    key.shadow.camera.left = -6;
    key.shadow.camera.right = 6;
    key.shadow.camera.top = 6;
    key.shadow.camera.bottom = -6;
    key.shadow.bias = -0.0008;
    this.scene.add(key);
    const rim = new PointLight(0x90a6c4, 1.5, 30);
    rim.position.set(-5, 2, -5);
    this.scene.add(rim);
    this.hotspot = new PointLight(0xff6a00, 0, 12);
    this.scene.add(this.hotspot);

    const ground = new Mesh(new PlaneGeometry(40, 40), new ShadowMaterial({ opacity: 0.35 }));
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);

    this.scene.add(this.stack);
    this.stack.add(this.patchGroup);
    this.rebuild();
    this.rebuildPatches();
    this.resize(canvas);
  }

  setGeometry(g: Partial<DeviceGeometry>) {
    this.geom = { ...this.geom, ...g };
    this.rebuild();
    this.rebuildPatches();
  }

  /** number of areal sub-populations (model K) */
  setPatchCount(K: number) {
    if (K === this.K) return;
    this.K = Math.max(2, Math.min(28, K));
    this.rebuildPatches();
  }

  /** ease toward a breakdown fraction phi_bar ∈ [0,1] */
  setBreakdown(phiBar: number) {
    this.targetPhi = Math.max(0, Math.min(1, phiBar));
  }

  /** replay the progressive breakdown from pristine (HRS) up to phi_bar */
  triggerBreakdown(phiBar: number) {
    this.phi = 0;
    this.targetPhi = Math.max(0, Math.min(1, phiBar));
  }

  peakTemperatureK(): number {
    return Math.round(300 + this.phi * 1100);
  }

  private hbnHeight(): number {
    return this.geom.hbnLayers * LAYER_H;
  }

  private rebuild() {
    for (const c of [...this.stack.children]) {
      if (c === this.patchGroup) continue;
      this.stack.remove(c);
      (c as Mesh).geometry?.dispose?.();
    }
    const ground = -this.hbnHeight() / 2;
    const topH = this.geom.topThickness;
    const botH = this.geom.bottomThickness;

    const bot = makeElectrode(botH, 0x9aa7b4, 0.55);
    bot.position.y = ground - botH / 2;
    bot.castShadow = bot.receiveShadow = true;
    this.stack.add(bot);

    const h = this.hbnHeight();
    for (let i = 0; i < this.geom.hbnLayers; i++) {
      const layer = new Mesh(
        new CylinderGeometry(RADIUS * 0.98, RADIUS * 0.98, LAYER_H * 0.82, 64),
        new MeshStandardMaterial({
          color: new Color(0x6f9fd0),
          roughness: 0.22,
          metalness: 0.0,
          transparent: true,
          opacity: 0.18, // see-through so interior patches read clearly
          depthWrite: false,
        })
      );
      layer.position.y = ground + LAYER_H * (i + 0.5);
      this.stack.add(layer);
    }

    const top = makeElectrode(topH, 0xd9b24a, 0.32, 0.42); // translucent top contact
    top.position.y = ground + h + topH / 2;
    top.castShadow = top.receiveShadow = true;
    this.stack.add(top);
  }

  private rebuildPatches() {
    for (const p of this.patches) {
      this.patchGroup.remove(p.mesh, p.halo);
      p.mesh.geometry.dispose();
    }
    this.patches = [];
    const h = this.hbnHeight();
    const ground = -h / 2;
    const cy = ground + h / 2;
    const GA = 2.399963; // golden angle — even areal spread
    for (let k = 0; k < this.K; k++) {
      const rad = RADIUS * 0.62 * Math.sqrt((k + 0.5) / this.K);
      const ang = k * GA;
      const x = rad * Math.cos(ang);
      const z = rad * Math.sin(ang);
      // deterministic pseudo-random threshold so patches break in a spread order
      const thr = 0.18 + 0.72 * frac(Math.sin(k * 12.9898) * 43758.5453);

      const mesh = new Mesh(
        new CylinderGeometry(0.12, 0.14, h, 18, 1, true),
        new MeshBasicMaterial({ color: 0x39404d, transparent: true, opacity: 0.65, toneMapped: false })
      );
      mesh.position.set(x, cy, z);

      const halo = new Sprite(
        new SpriteMaterial({
          map: this.glowTex,
          color: 0xff8a2a,
          blending: AdditiveBlending,
          depthWrite: false,
          transparent: true,
          opacity: 0,
          toneMapped: false,
        })
      );
      halo.position.set(x, cy, z);
      halo.scale.set(1.0, h * 1.7, 1);

      this.patchGroup.add(mesh, halo);
      this.patches.push({ mesh, halo, thr });
    }
  }

  resize(canvas: HTMLCanvasElement) {
    const w = canvas.clientWidth || 600;
    const hgt = canvas.clientHeight || 600;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(w, hgt, false);
    this.camera.aspect = w / Math.max(1, hgt);
    this.camera.updateProjectionMatrix();
  }

  render(dt: number) {
    this.phi += (this.targetPhi - this.phi) * Math.min(1, dt * 2.5);
    const phi = this.phi;

    for (const p of this.patches) {
      // smooth per-patch turn-on around its threshold
      const a = smoothstep(p.thr - 0.12, p.thr + 0.12, phi);
      const col = forgeRamp(0.3 + 0.5 * a);
      const m = p.mesh.material as MeshBasicMaterial;
      if (a < 0.02) {
        m.color.setHex(0x2a2f3a); // pristine (dark)
        m.opacity = 0.5;
      } else {
        m.color.copy(col);
        m.opacity = 0.6 + 0.4 * a;
      }
      const hm = p.halo.material as SpriteMaterial;
      hm.color.copy(col);
      hm.opacity = 0.95 * a;
      const s = 0.85 + 0.7 * a;
      p.halo.scale.set(s, this.hbnHeight() * 1.7, 1);
    }

    this.hotspot.color.copy(forgeRamp(0.3 + 0.5 * phi));
    this.hotspot.intensity = phi * 16;
    this.hotspot.position.y = 0;

    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

function makeElectrode(height: number, color: number, roughness: number, opacity = 1): Mesh {
  const mat = new MeshStandardMaterial({ color, metalness: 1.0, roughness });
  if (opacity < 1) {
    mat.transparent = true;
    mat.opacity = opacity;
  }
  return new Mesh(new CylinderGeometry(RADIUS, RADIUS, height, 64), mat);
}

function smoothstep(a: number, b: number, x: number): number {
  const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
}
function frac(x: number): number {
  return x - Math.floor(x);
}

function makeGlowTexture(): Texture {
  const s = 128;
  const c = document.createElement('canvas');
  c.width = c.height = s;
  const ctx = c.getContext('2d')!;
  const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.35, 'rgba(255,255,255,0.55)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, s, s);
  return new CanvasTexture(c);
}

function makeGradientTexture(): Texture {
  const c = document.createElement('canvas');
  c.width = 2;
  c.height = 256;
  const ctx = c.getContext('2d')!;
  const g = ctx.createLinearGradient(0, 0, 0, 256);
  g.addColorStop(0, '#0e131b');
  g.addColorStop(0.5, '#0a0d12');
  g.addColorStop(1, '#06080b');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 2, 256);
  return new CanvasTexture(c);
}
