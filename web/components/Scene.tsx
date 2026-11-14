'use client';
import * as THREE from 'three';
import { Suspense, useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {
  AccumulativeShadows, CameraControls, ContactShadows, Environment, Html, Lightformer, Line, RandomizedLight,
  useGLTF, useProgress, useTexture,
} from '@react-three/drei';
import { EffectComposer, N8AO, ToneMapping } from '@react-three/postprocessing';
import { ToneMappingMode } from 'postprocessing';
import { Config, FABRICS, HOTSPOTS, SCENES, VIEWS } from '../lib/options';

const DRACO = '/draco/';
useGLTF.preload('/models/sofa.glb', DRACO);
useGLTF.preload('/models/frame.glb', DRACO);

const TEX_URLS = {
  boucleN: '/textures/boucle_normal.png', boucleC: '/textures/boucle_color.png',
  velvetN: '/textures/velvet_normal.png', velvetC: '/textures/velvet_color.png',
  linenN: '/textures/linen_normal.png', linenC: '/textures/linen_color.png',
  leatherN: '/textures/leather_normal.png', leatherC: '/textures/leather_color.png',
  oakN: '/textures/oak_normal.png', oakC: '/textures/oak_color.png',
};
type Maps = Record<keyof typeof TEX_URLS, THREE.Texture>;

function useMaps(): Maps {
  const t = useTexture(TEX_URLS) as Maps;
  useMemo(() => {
    for (const [k, tex] of Object.entries(t)) {
      tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
      tex.anisotropy = 8;
      tex.flipY = false;
      tex.colorSpace = k.endsWith('C') ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      const fk = k.replace(/[NC]$/, '') as keyof typeof FABRICS;
      const rep = FABRICS[fk]?.repeat ?? 1;
      tex.repeat.set(rep, rep);
      tex.needsUpdate = true;
    }
  }, [t]);
  return t;
}

function fabricMaterial(maps: Maps, key: keyof typeof FABRICS, hex: string, mat?: THREE.MeshPhysicalMaterial) {
  const f = FABRICS[key];
  const m = mat ?? new THREE.MeshPhysicalMaterial();
  m.map = maps[`${key}C` as keyof Maps]; m.normalMap = maps[`${key}N` as keyof Maps];
  m.normalScale.set(f.normalScale, f.normalScale);
  m.color.set(hex);
  m.roughness = f.roughness;
  m.sheen = f.sheen; m.sheenRoughness = f.sheenRoughness;
  m.sheenColor.set(hex).lerp(new THREE.Color('#ffffff'), f.sheenLift);
  m.clearcoat = f.clearcoat ?? 0; m.clearcoatRoughness = 0.45;
  m.needsUpdate = true;
  return m;
}

function Sofa({ cfg, xray }: { cfg: Config; xray: boolean }) {
  const { scene } = useGLTF('/models/sofa.glb', DRACO);
  const maps = useMaps();
  const shell = useMemo(() => new THREE.MeshPhysicalMaterial(), []);
  const cushion = useMemo(() => new THREE.MeshPhysicalMaterial(), []);
  const wood = useMemo(() => new THREE.MeshPhysicalMaterial({ roughness: 0.42, clearcoat: 0.35, clearcoatRoughness: 0.35 }), []);
  const glide = useMemo(() => new THREE.MeshStandardMaterial({ color: '#1d1d1d', roughness: 1 }), []);
  const pillows = useMemo(() => {
    const p = {
      GreyBoucle: fabricMaterial(maps, 'boucle', '#8f8a84'),
      RustVelvet: fabricMaterial(maps, 'velvet', '#7d2f14'),
      Linen: fabricMaterial(maps, 'linen', '#cdbfa8'),
    };
    Object.values(p).forEach((m) => { m.side = THREE.DoubleSide; });
    return p;
  }, [maps]);

  useEffect(() => {
    fabricMaterial(maps, cfg.fabric, cfg.colour, shell);
    fabricMaterial(maps, cfg.fabric, cfg.cushion ?? cfg.colour, cushion);
    for (const m of [shell, cushion]) {
      m.transparent = xray; m.opacity = xray ? 0.14 : 1; m.depthWrite = !xray; m.needsUpdate = true;
    }
  }, [cfg.fabric, cfg.colour, cfg.cushion, xray, maps, shell, cushion]);

  useEffect(() => {
    wood.map = maps.oakC; wood.normalMap = maps.oakN; wood.normalScale.set(0.4, 0.4);
    wood.color.set(cfg.leg); wood.needsUpdate = true;
  }, [cfg.leg, maps, wood]);

  // layout effect: assign materials BEFORE AccumulativeShadows snapshots them (it restores the snapshot each pass)
  useLayoutEffect(() => {
    scene.traverse((o: any) => {
      if (!o.isMesh) return;
      o.castShadow = true; o.receiveShadow = true;
      const n: string = o.name;
      if (n.startsWith('Fabric_Seat') || n.startsWith('Fabric_Back')) o.material = cushion;
      else if (n.startsWith('Fabric_')) o.material = shell;
      else if (n.startsWith('Leg_')) o.material = wood;
      else if (n.startsWith('Glide_')) o.material = glide;
      else if (n.startsWith('Pillow_')) {
        const key = n.split('_')[1] as keyof typeof pillows;
        o.material = pillows[key] ?? o.material;
        o.visible = cfg.pillows && !xray;
      }
    });
  }, [scene, shell, cushion, wood, glide, pillows, cfg.pillows, xray]);

  return <primitive object={scene} />;
}

function Frame({ visible }: { visible: boolean }) {
  const { scene } = useGLTF('/models/frame.glb', DRACO);
  return <primitive object={scene} visible={visible} />;
}

// ---------------------------------------------------------------- room scenes
/** Procedural oak plank floor: staggered boards, per-board tone, fine grain, bevelled joints (colour + bump). */
function makePlankTextures() {
  const S = 2048, rows = 12, rnd = (() => { let s = 7; return () => ((s = (s * 16807) % 2147483647) / 2147483647); })();
  const c = document.createElement('canvas'); c.width = c.height = S; const x = c.getContext('2d')!;
  const b = document.createElement('canvas'); b.width = b.height = S; const y = b.getContext('2d')!;
  y.fillStyle = '#808080'; y.fillRect(0, 0, S, S);
  const rh = S / rows;
  for (let r = 0; r < rows; r++) {
    let px = -rnd() * S * 0.5;
    while (px < S) {
      const len = S * (0.35 + rnd() * 0.45);
      const l = 0.82 + rnd() * 0.3, hue = 28 + rnd() * 6;
      x.fillStyle = `hsl(${hue}, ${38 + rnd() * 10}%, ${46 * l}%)`;
      x.fillRect(px, r * rh, len, rh);
      for (let g = 0; g < 46; g++) {                        // grain lines
        const gy = r * rh + rnd() * rh, a = 0.04 + rnd() * 0.08;
        x.strokeStyle = `rgba(${rnd() < 0.5 ? '60,35,15' : '255,235,200'},${a})`; x.lineWidth = 1 + rnd() * 2;
        x.beginPath(); x.moveTo(px, gy);
        for (let k = 0; k <= 8; k++) x.lineTo(px + (len * k) / 8, gy + Math.sin(k * 0.9 + g) * rnd() * 3);
        x.stroke();
      }
      if (rnd() < 0.25) {                                    // knot
        x.fillStyle = 'rgba(70,40,20,0.25)'; x.beginPath();
        x.ellipse(px + rnd() * len, r * rh + rh / 2, 14 + rnd() * 10, 6, 0, 0, Math.PI * 2); x.fill();
      }
      y.fillStyle = '#5a5a5a'; y.fillRect(px - 2, r * rh, 4, rh);           // end joint
      px += len;
    }
    y.fillStyle = '#4a4a4a'; y.fillRect(0, r * rh - 2, S, 4);               // long joint
  }
  const map = new THREE.CanvasTexture(c); map.colorSpace = THREE.SRGBColorSpace;
  const bump = new THREE.CanvasTexture(b);
  for (const tx of [map, bump]) { tx.wrapS = tx.wrapT = THREE.RepeatWrapping; tx.repeat.set(5, 5); tx.anisotropy = 16; }
  return { map, bump };
}

/** Table lamp with turned ceramic base, brass fittings and a translucent linen drum shade. */
function TableLamp({ on }: { on: boolean }) {
  const base = useMemo(() => new THREE.LatheGeometry([
    [0.0, 0], [0.07, 0], [0.075, 0.008], [0.06, 0.02], [0.085, 0.07], [0.11, 0.15], [0.105, 0.23], [0.075, 0.29],
    [0.035, 0.32], [0.03, 0.335], [0.0, 0.335],
  ].map(([r, h]) => new THREE.Vector2(r, h)), 64), []);
  const shade = useMemo(() => new THREE.LatheGeometry([
    [0.19, 0], [0.191, 0.004], [0.14, 0.24], [0.139, 0.244], [0.137, 0.24], [0.188, 0.004], [0.187, 0],
  ].map(([r, h]) => new THREE.Vector2(r, h)), 72), []);
  return (
    <group>
      <mesh geometry={base} castShadow receiveShadow>
        <meshPhysicalMaterial color="#d8d2c4" roughness={0.32} clearcoat={0.6} clearcoatRoughness={0.25} />
      </mesh>
      <mesh position={[0, 0.36, 0]} castShadow><cylinderGeometry args={[0.012, 0.012, 0.05, 24]} /><meshStandardMaterial color="#b08a4a" metalness={1} roughness={0.28} /></mesh>
      <mesh position={[0, 0.405, 0]}><cylinderGeometry args={[0.022, 0.016, 0.04, 24]} /><meshStandardMaterial color="#b08a4a" metalness={1} roughness={0.28} /></mesh>
      <mesh position={[0, 0.46, 0]}><sphereGeometry args={[0.032, 24, 16]} />
        <meshStandardMaterial color="#fff6e8" emissive="#ffd9a8" emissiveIntensity={on ? 6 : 0} roughness={0.4} /></mesh>
      {/* harp */}
      {[-1, 1].map((s) => (
        <mesh key={s} position={[s * 0.07, 0.49, 0]} rotation-z={s * 0.5}><cylinderGeometry args={[0.003, 0.003, 0.17, 8]} /><meshStandardMaterial color="#b08a4a" metalness={1} roughness={0.3} /></mesh>
      ))}
      <mesh geometry={shade} position={[0, 0.35, 0]} castShadow>
        <meshPhysicalMaterial color="#eee4d2" roughness={0.95} side={THREE.DoubleSide} transmission={0.25} thickness={0.002}
          emissive="#ffcf96" emissiveIntensity={on ? 0.55 : 0.0} />
      </mesh>
      <mesh position={[0, 0.6, 0]}><sphereGeometry args={[0.012, 16, 12]} /><meshStandardMaterial color="#b08a4a" metalness={1} roughness={0.3} /></mesh>
      {on && <pointLight position={[0, 0.46, 0]} intensity={1.8} distance={4} decay={2} color="#ffc68a" castShadow={false} />}
    </group>
  );
}
function Room({ kind }: { kind: string }) {
  const maps = useMaps();
  const floorMaps = useMemo(() => {
    const c = maps.oakC.clone(); const n = maps.oakN.clone();
    for (const t of [c, n]) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(26, 26); t.needsUpdate = true; }
    return { c, n };
  }, [maps]);
  const planks = useMemo(() => makePlankTextures(), []);
  const rugMaps = useMemo(() => {
    const c = maps.linenC.clone(); const n = maps.linenN.clone();
    for (const t of [c, n]) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(24, 16); t.needsUpdate = true; }
    return { c, n };
  }, [maps]);
  if (kind === 'studio') return null;
  const evening = kind === 'evening';
  const wall = evening ? '#c9bcab' : '#d6d0c6';
  return (
    <group>
      <mesh rotation-x={-Math.PI / 2} position={[0, -0.001, 0]} receiveShadow>
        <planeGeometry args={[14, 14]} />
        <meshPhysicalMaterial map={planks.map} bumpMap={planks.bump} bumpScale={0.6} color={evening ? '#c9a888' : '#ffffff'}
          roughness={0.45} clearcoat={0.2} clearcoatRoughness={0.4} />
      </mesh>
      <mesh rotation-x={-Math.PI / 2} position={[0.1, 0.002, 0.55]} receiveShadow>
        <planeGeometry args={[3.2, 2.2]} />
        <meshStandardMaterial map={rugMaps.c} normalMap={rugMaps.n} color={evening ? '#b8ad9c' : '#e2dbd0'} roughness={1} />
      </mesh>
      <mesh position={[0, 1.6, -0.95]} receiveShadow>
        <planeGeometry args={[14, 3.2]} />
        <meshStandardMaterial color={wall} roughness={0.9} />
      </mesh>
      <mesh position={[0, 0.06, -0.94]}>
        <boxGeometry args={[14, 0.12, 0.02]} />
        <meshStandardMaterial color={wall} roughness={0.6} />
      </mesh>
      {/* panel mouldings */}
      {[-3.3, -1.65, 0, 1.65, 3.3].map((x) => (
        <group key={x} position={[x, 1.55, -0.935]}>
          {[[0, 0.75, 1.3, 0.025], [0, -0.75, 1.3, 0.025], [-0.64, 0, 0.025, 1.5], [0.64, 0, 0.025, 1.5]].map(([px, py, w, h], i) => (
            <mesh key={i} position={[px, py, 0]}><boxGeometry args={[w, h, 0.018]} /><meshStandardMaterial color={wall} roughness={0.6} /></mesh>
          ))}
        </group>
      ))}
      {/* side table (walnut, turned pedestal) + table lamp */}
      <group position={[-1.38, 0, -0.32]}>
        <mesh castShadow receiveShadow geometry={new THREE.LatheGeometry([[0, 0], [0.17, 0], [0.17, 0.02], [0.06, 0.05], [0.04, 0.3], [0.05, 0.5], [0.08, 0.52], [0, 0.52]].map(([r, h]) => new THREE.Vector2(r, h)), 48)}>
          <meshPhysicalMaterial color="#5b3a22" roughness={0.42} clearcoat={0.4} clearcoatRoughness={0.3} />
        </mesh>
        <mesh position={[0, 0.535, 0]} castShadow receiveShadow><cylinderGeometry args={[0.25, 0.245, 0.03, 64]} />
          <meshPhysicalMaterial color="#5b3a22" roughness={0.35} clearcoat={0.5} clearcoatRoughness={0.2} /></mesh>
        <group position={[0, 0.55, 0]}><TableLamp on={evening} /></group>
        <mesh position={[0.13, 0.565, 0.1]} rotation-y={0.4} castShadow><boxGeometry args={[0.15, 0.03, 0.2]} /><meshStandardMaterial color="#2f3a40" roughness={0.7} /></mesh>
      </group>      {/* framed print + floor vase */}
      <group position={[0.15, 1.45, -0.93]}>
        <mesh><boxGeometry args={[0.9, 0.66, 0.03]} /><meshStandardMaterial color="#6b4a30" roughness={0.5} /></mesh>
        <mesh position={[0, 0, 0.017]}><planeGeometry args={[0.82, 0.58]} /><meshStandardMaterial color="#ece6dc" roughness={0.95} /></mesh>
        <mesh position={[-0.13, 0.06, 0.019]}><circleGeometry args={[0.13, 48]} /><meshStandardMaterial color="#2a2623" roughness={0.9} /></mesh>
        <mesh position={[0.14, -0.12, 0.019]}><circleGeometry args={[0.15, 48, 0, Math.PI]} /><meshStandardMaterial color="#a4542e" roughness={0.9} /></mesh>
      </group>
      <group position={[1.4, 0, -0.62]}>
        <mesh position={[0, 0.3, 0]} castShadow receiveShadow><cylinderGeometry args={[0.13, 0.18, 0.6, 48]} /><meshStandardMaterial color="#d9d2c6" roughness={0.55} /></mesh>
        {[[-0.06, 0.25], [0.05, -0.2], [0.0, 0.05]].map(([x, r], i) => (
          <mesh key={i} position={[x, 0.95 + i * 0.05, 0]} rotation-z={r}><cylinderGeometry args={[0.006, 0.008, 0.75, 6]} /><meshStandardMaterial color="#5a4632" roughness={0.8} /></mesh>
        ))}
      </group>    </group>
  );
}

function Lights({ kind }: { kind: string }) {
  const evening = kind === 'evening';
  return (
    <>
      <ambientLight intensity={evening ? 0.08 : 0.15} />
      <directionalLight userData={{ rasterOnly: true }} position={[-3, 4.5, 3.5]} intensity={evening ? 0.9 : 1.5} color={evening ? '#ffdcb8' : '#fff3e6'} />
      <directionalLight userData={{ rasterOnly: true }} position={[3.5, 2, -2]} intensity={evening ? 0.25 : 0.5} color="#e8eeff" />
      <Environment resolution={256} frames={1} key={kind}>
        <Lightformer form="rect" intensity={evening ? 0.8 : 2.2} position={[0, 4.5, 1]} rotation-x={Math.PI / 2} scale={[7, 4, 1]} />
        <Lightformer form="rect" intensity={evening ? 1.5 : 1.6} color={evening ? '#ffc08a' : '#ffffff'}
          position={[-4.5, 1.6, 2.5]} rotation-y={Math.PI / 2.4} scale={[4, 2.4, 1]} />
        <Lightformer form="rect" intensity={evening ? 0.3 : 0.9} position={[4.5, 1.5, -1]} rotation-y={-Math.PI / 2} scale={[4, 2, 1]} />
        <Lightformer form="ring" intensity={evening ? 0.6 : 1.2} color="#ffe6cc" position={[2.5, 2.5, 4]} scale={2.2} />
      </Environment>
    </>
  );
}

// ---------------------------------------------------------------- overlays (always mounted; React 19 + drei Html)
function Hotspots({ show, active, onPick }: { show: boolean; active: string | null; onPick: (id: string | null) => void }) {
  return (
    <>
      {HOTSPOTS.map((h, i) => (
        <Html key={h.id} position={h.pos} center zIndexRange={[20, 0]} occlude>
          <button className={`hotspot${active === h.id ? ' on' : ''}`} style={{ display: show ? undefined : 'none' }}
            tabIndex={show ? 0 : -1} onClick={() => onPick(active === h.id ? null : h.id)} aria-label={h.title}>{i + 1}</button>
        </Html>
      ))}
    </>
  );
}

function Dim({ a, b, label, show }: { a: [number, number, number]; b: [number, number, number]; label: string; show: boolean }) {
  const mid = a.map((v, i) => (v + b[i]) / 2) as [number, number, number];
  return (
    <group>
      <group visible={show}><Line points={[a, b]} color="#1d1a17" lineWidth={1.5} /></group>
      <Html position={mid} center zIndexRange={[10, 0]}><span className="dimlabel" style={{ display: show ? undefined : 'none' }}>{label}</span></Html>
    </group>
  );
}

function Dimensions({ show }: { show: boolean }) {
  return (
    <group userData={{ rasterOnly: true }}>
      <Dim show={show} a={[-0.95, 0.88, 0.47]} b={[0.95, 0.88, 0.47]} label="190 cm wide" />
      <Dim show={show} a={[1.08, 0, 0.47]} b={[1.08, 0.78, 0.47]} label="78 cm high" />
      <Dim show={show} a={[1.08, 0.005, -0.45]} b={[1.08, 0.005, 0.45]} label="90 cm deep" />
      <Dim show={show} a={[-1.08, 0, 0.47]} b={[-1.08, 0.445, 0.47]} label="seat 44.5 cm" />
    </group>
  );
}

function Rig({ view, autoRotate, onUserMove }: { view: { name: string; n: number }; autoRotate: boolean; onUserMove: () => void }) {
  const ref = useRef<CameraControls>(null);
  const aspect = useThree((s) => s.size.width / Math.max(1, s.size.height));
  useEffect(() => {
    const v = VIEWS[view.name] ?? VIEWS.hero;
    const k = view.name === 'detail' ? 1 : Math.min(2.1, Math.max(1, 1.45 / aspect));
    const p = v.pos.map((c, i) => v.target[i] + (c - v.target[i]) * k) as [number, number, number];
    ref.current?.setLookAt(...p, ...v.target, view.n > 0);
  }, [view]); // eslint-disable-line react-hooks/exhaustive-deps
  useFrame((_, d) => { if (autoRotate && ref.current) ref.current.rotate(d * 0.22, 0, false); });
  return (
    <CameraControls ref={ref} makeDefault minDistance={1.25} maxDistance={6.5}
      minPolarAngle={0.08} maxPolarAngle={Math.PI / 2 - 0.03} truckSpeed={0} smoothTime={0.35} onStart={onUserMove} />
  );
}

// ---------------------------------------------------------------- high-resolution photo capture
export interface RenderOpts {
  photoreal?: boolean;          // path traced (Cycles-like) instead of the fast raster render
  samples?: number;             // path-tracing samples per pixel
  denoise?: boolean;
  onProgress?: (samples: number, total: number, preview: HTMLCanvasElement) => void;
  shouldStop?: () => 'finish' | 'cancel' | null;
}
export type RenderFn = (w: number, h: number, opts?: RenderOpts) => Promise<string | null>;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Seamless studio cyclorama: floor sweeping up into a back wall (only used while path tracing). */
function makeCyclorama(color: string) {
  const prof: [number, number][] = [[7, 0], [2, 0], [-1.6, 0]];
  const R = 1.6;
  for (let i = 1; i <= 12; i++) { const a = (i / 12) * Math.PI / 2; prof.push([-1.6 - R * Math.sin(a), R - R * Math.cos(a)]); }
  prof.push([-3.2, 6]);
  const W = 9, pos: number[] = [], idx: number[] = [];
  prof.forEach(([z, y]) => { pos.push(-W, y, z, W, y, z); });
  for (let i = 0; i < prof.length - 1; i++) { const k = i * 2; idx.push(k, k + 2, k + 1, k + 1, k + 2, k + 3); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color, roughness: 0.92, side: THREE.DoubleSide }));
  m.name = 'PT_Cyclorama';
  return m;
}

/** Progressive path tracing with three-gpu-pathtracer (BVH + MIS + multi-bounce, like Blender Cycles). */
async function pathTrace(st: any, kind: string, bg: string, opts: RenderOpts): Promise<string | null> {
  // three r187 removed this chunk; the path tracer's cube->equirect shader only needs textureCube, so an empty chunk is safe
  const SC = THREE.ShaderChunk as Record<string, string>;
  if (SC.cube_uv_reflection_fragment === undefined) SC.cube_uv_reflection_fragment = '';
  const { WebGLPathTracer, DenoiseMaterial } = await import('three-gpu-pathtracer');
  const { FullScreenQuad } = await import('three/examples/jsm/postprocessing/Pass.js');
  const gl: THREE.WebGLRenderer = st.gl; const scene: THREE.Scene = st.scene; const camera = st.camera;
  const total = opts.samples ?? 256;

  // raster-only helpers (fake shadow catchers, dimension lines, sharp sun lights) are replaced by real light transport
  const hidden: THREE.Object3D[] = [];
  scene.traverse((o) => { if (o.userData?.rasterOnly && o.visible) { o.visible = false; hidden.push(o); } });
  const cyc = kind === 'studio' ? makeCyclorama(bg) : null;
  if (cyc) scene.add(cyc);
  const prevEnvI = scene.environmentIntensity; scene.environmentIntensity = kind === 'evening' ? 1.5 : 1.7;
  const prevTM = gl.toneMapping, prevExp = gl.toneMappingExposure;
  gl.toneMapping = THREE.AgXToneMapping; gl.toneMappingExposure = kind === 'evening' ? 1.25 : 1.1;   // Blender's default view transform

  const pt: any = new WebGLPathTracer(gl);
  pt.bounces = 8; pt.transmissiveBounces = 6; pt.filterGlossyFactor = 0.4; pt.multipleImportanceSampling = true;
  pt.minSamples = 1; pt.renderDelay = 0; pt.fadeDuration = 0; pt.rasterizeScene = false; pt.dynamicLowRes = false;
  pt.renderScale = 1; pt.tiles.set(2, 2);
  const dq = new FullScreenQuad(new DenoiseMaterial({
    map: null, blending: THREE.NoBlending, premultipliedAlpha: gl.getContextAttributes()?.premultipliedAlpha ?? true,
  }) as any);
  (dq.material as any).sigma = 2.2; (dq.material as any).threshold = 0.05; (dq.material as any).kSigma = 1.0;
  pt.renderToCanvasCallback = (_t: any, renderer: any, quad: any) => {
    if (opts.denoise !== false && pt.samples >= 4) { (dq.material as any).map = quad.material.map; dq.render(renderer); }
    else { const ac = renderer.autoClear; renderer.autoClear = false; quad.render(renderer); renderer.autoClear = ac; }
  };

  const preview = document.createElement('canvas');
  const pw = 640; preview.width = pw; preview.height = Math.round(pw * gl.domElement.height / gl.domElement.width);
  const pctx = preview.getContext('2d')!;
  let result: string | null = null;
  try {
    pt.setScene(scene, camera);
    const t0 = performance.now(); let last = 0;
    while (pt.samples < total) {
      const stop = opts.shouldStop?.();
      if (stop === 'cancel') return null;
      if (stop === 'finish' && pt.samples >= 1) break;
      pt.renderSample();
      if (pt.isCompiling && performance.now() - t0 > 120000) throw new Error('Path tracer shader did not compile');
      const now = performance.now();
      if (now - last > 400) {
        last = now;
        pctx.drawImage(gl.domElement, 0, 0, preview.width, preview.height);
        opts.onProgress?.(pt.samples, total, preview);
      }
      await sleep(0);                                    // keep the page responsive
    }
    pt.renderSample();
    pctx.drawImage(gl.domElement, 0, 0, preview.width, preview.height);
    opts.onProgress?.(pt.samples, total, preview);          // report the final sample count
    result = gl.domElement.toDataURL('image/jpeg', 0.95);
  } finally {
    pt.dispose(); dq.dispose();
    hidden.forEach((o) => { o.visible = true; });
    if (cyc) { scene.remove(cyc); cyc.geometry.dispose(); (cyc.material as THREE.Material).dispose(); }
    scene.environmentIntensity = prevEnvI;
    gl.toneMapping = prevTM; gl.toneMappingExposure = prevExp;
  }
  return result;
}

function Capture({ register, kind, bg }: { register: (fn: RenderFn) => void; kind: string; bg: string }) {
  const get = useThree((s) => s.get);
  const env = useRef({ kind, bg }); env.current = { kind, bg };
  useEffect(() => {
    register(async (w, h, opts = {}) => {
      const st = get();
      const prev = { ...st.size }; const prevDpr = st.viewport.dpr; const prevLoop = st.frameloop;
      st.setFrameloop('never');
      st.setDpr(1);
      st.setSize(w, h, prev.top, prev.left);
      await sleep(150);                                   // let React effects resize camera + composer
      try {
        if (opts.photoreal) return await pathTrace(get(), env.current.kind, env.current.bg, opts);
        for (let i = 0; i < 10; i++) { get().advance(performance.now() + i * 16); await sleep(0); }
        return get().gl.domElement.toDataURL('image/jpeg', 0.95);
      } finally {
        st.setSize(prev.width, prev.height, prev.top, prev.left);
        st.setDpr(prevDpr);
        await sleep(30);
        st.setFrameloop(prevLoop);
      }
    });
  }, [get, register]);
  return null;
}
function Loader() {
  const { progress, active } = useProgress();
  if (!active && progress >= 100) return null;
  return (
    <div className="loader-wrap" aria-live="polite">
      <div className="loader"><span style={{ width: `${progress}%` }} />Loading sofa {progress.toFixed(0)}%</div>
    </div>
  );
}

export interface SceneProps {
  cfg: Config; xray: boolean; dims: boolean; hotspots: boolean; autoRotate: boolean;
  view: { name: string; n: number }; activeHotspot: string | null;
  onHotspot: (id: string | null) => void; onUserMove: () => void; onReady: (canvas: HTMLCanvasElement) => void;
  registerRender: (fn: RenderFn) => void;
}

export default function Scene(p: SceneProps) {
  const kind = p.cfg.scene;
  const bg = kind === 'studio' ? p.cfg.backdrop : SCENES[kind].bg;
  const dark = new THREE.Color(bg).getHSL({ h: 0, s: 0, l: 0 }).l < 0.35;
  return (
    <>
      <Canvas
        shadows dpr={[1, 2]}
        camera={{ fov: 32, position: VIEWS.hero.pos, near: 0.05, far: 60 }}
        gl={{ antialias: true, preserveDrawingBuffer: true }}
        onCreated={({ gl }) => { gl.toneMapping = THREE.NoToneMapping; p.onReady(gl.domElement); }}
      >
        <color attach="background" args={[bg]} />
        {kind === 'studio' && <fog attach="fog" args={[bg, 8, 18]} />}
        <Lights kind={kind} />
        <Suspense fallback={null}>
          <Sofa cfg={p.cfg} xray={p.xray} />
          <Frame visible={p.xray} />
          <Room kind={kind} />
          <Hotspots show={p.hotspots} active={p.activeHotspot} onPick={p.onHotspot} />
          <Dimensions show={p.dims} />
          {/* soft, physically-plausible ground shadows accumulated from many light positions */}
          <group userData={{ rasterOnly: true }}>
          <AccumulativeShadows key={`${kind}-${p.cfg.pillows}-${p.xray}`} temporal frames={90} alphaTest={0.7}
            opacity={dark ? 1 : 0.85} scale={7} color="#22150c" colorBlend={0.6} position={[0, 0.004, 0]}>
            <RandomizedLight amount={8} radius={3.2} ambient={0.55} intensity={1.1} position={[-2.5, 5, 3]} bias={0.0008} mapSize={1024} />
          </AccumulativeShadows>
          </group>
        </Suspense>
        <group userData={{ rasterOnly: true }}><ContactShadows position={[0, 0.003, 0]} scale={6} resolution={1024} blur={1.2} opacity={0.35} far={0.25} color="#1a120c" /></group>
        <Rig view={p.view} autoRotate={p.autoRotate} onUserMove={p.onUserMove} />
        <Capture register={p.registerRender} kind={kind} bg={bg} />
        <EffectComposer multisampling={8}>
          <N8AO aoRadius={0.35} intensity={2.4} distanceFalloff={0.6} quality="high" />
          <ToneMapping mode={ToneMappingMode.NEUTRAL} />
        </EffectComposer>
      </Canvas>
      <Loader />
    </>
  );
}
