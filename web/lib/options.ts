// Product options for the Caramel Shell 2S configurator.

export type FabricKey = 'boucle' | 'velvet' | 'linen' | 'leather';

export interface Swatch { name: string; hex: string }

export interface Fabric {
  key: FabricKey;
  label: string;
  blurb: string;
  roughness: number;
  sheen: number;
  sheenRoughness: number;
  sheenLift: number;      // how much the sheen colour is lifted towards white
  normalScale: number;
  repeat: number;          // texture tiles per 120 mm
  clearcoat?: number;
  colours: Swatch[];
}

export const FABRICS: Record<FabricKey, Fabric> = {
  boucle: {
    key: 'boucle', label: 'Bouclé', blurb: 'Dense looped bouclé, about 600 g/m², rated for 40,000+ rubs.',
    roughness: 0.96, sheen: 0.55, sheenRoughness: 0.55, sheenLift: 0.35, normalScale: 1.7, repeat: 1,
    colours: [
      { name: 'Caramel', hex: '#9a5a26' }, { name: 'Ivory', hex: '#e4ddcd' }, { name: 'Oat', hex: '#c8b496' },
      { name: 'Sage', hex: '#8b977a' }, { name: 'Terracotta', hex: '#a9543a' }, { name: 'Blush', hex: '#d6b0a2' },
      { name: 'Charcoal', hex: '#45423e' },
    ],
  },
  velvet: {
    key: 'velvet', label: 'Velvet', blurb: 'Soft cotton-blend velvet with a deep, light-catching pile.',
    roughness: 0.78, sheen: 1, sheenRoughness: 0.32, sheenLift: 0.45, normalScale: 0.35, repeat: 0.5,
    colours: [
      { name: 'Rust', hex: '#8c3b1c' }, { name: 'Emerald', hex: '#1f5040' }, { name: 'Midnight', hex: '#1f2a46' },
      { name: 'Mustard', hex: '#b8862b' }, { name: 'Dusty pink', hex: '#c49890' }, { name: 'Mocha', hex: '#5c3f30' },
    ],
  },
  linen: {
    key: 'linen', label: 'Linen', blurb: 'Washed linen blend with a relaxed, natural slub.',
    roughness: 0.92, sheen: 0.3, sheenRoughness: 0.7, sheenLift: 0.2, normalScale: 0.8, repeat: 1,
    colours: [
      { name: 'Natural', hex: '#cdbfa8' }, { name: 'Chalk', hex: '#e9e5dc' }, { name: 'Stone', hex: '#a69e90' },
      { name: 'Olive', hex: '#6f6e4f' }, { name: 'Slate', hex: '#5d6670' },
    ],
  },
  leather: {
    key: 'leather', label: 'Leather', blurb: 'Semi-aniline leather with a soft pebbled grain.',
    roughness: 0.55, sheen: 0.15, sheenRoughness: 0.6, sheenLift: 0.2, normalScale: 1.1, repeat: 1.6, clearcoat: 0.3,
    colours: [
      { name: 'Cognac', hex: '#8b4a22' }, { name: 'Tan', hex: '#b07a4a' }, { name: 'Chocolate', hex: '#4a2c1d' },
      { name: 'Oxblood', hex: '#5c1f1d' }, { name: 'Black', hex: '#1f1d1c' },
    ],
  },
};

export const LEGS: Swatch[] = [
  { name: 'Natural oak', hex: '#c79c6c' },
  { name: 'Whitewashed oak', hex: '#e2d3bd' },
  { name: 'Walnut', hex: '#5e3c25' },
  { name: 'Black ash', hex: '#2a2725' },
];

export const BACKDROPS: Swatch[] = [
  { name: 'Warm grey', hex: '#cfcac3' },
  { name: 'Soft white', hex: '#efece7' },
  { name: 'Stone', hex: '#a7a198' },
  { name: 'Charcoal', hex: '#2c2b29' },
];

// Camera presets: position and target in metres (sofa front faces +Z, floor at y = 0)
export const VIEWS: Record<string, { label: string; pos: [number, number, number]; target: [number, number, number] }> = {
  hero: { label: '3/4', pos: [-2.3, 1.35, 3.0], target: [0, 0.38, 0] },
  front: { label: 'Front', pos: [0, 0.75, 3.7], target: [0, 0.4, 0] },
  side: { label: 'Side', pos: [-3.6, 0.7, 0.05], target: [0, 0.4, 0] },
  back: { label: 'Back', pos: [1.9, 1.2, -3.2], target: [0, 0.38, 0] },
  top: { label: 'Top', pos: [0, 4.3, 0.35], target: [0, 0.3, 0] },
  detail: { label: 'Close-up', pos: [-1.55, 0.95, 1.25], target: [-0.75, 0.5, 0.2] },
};

export const HOTSPOTS = [
  { id: 'fabric', pos: [0.36, 0.47, 0.06] as [number, number, number], title: 'Upholstery',
    text: 'Zip-off cushion covers. Choose bouclé, velvet, linen or leather in the panel.' },
  { id: 'arm', pos: [-0.84, 0.67, 0.16] as [number, number, number], title: 'Sculpted shell',
    text: 'The arms curve up into the back as one continuous shell, with firm and soft foam over a bent-ply skin.' },
  { id: 'back', pos: [-0.36, 0.67, -0.14] as [number, number, number], title: 'Lumbar back cushions',
    text: 'Soft HR30 foam with a lumbar crown, wrapped in compartmented fibre so it stays plump.' },
  { id: 'seat', pos: [0.0, 0.22, 0.45] as [number, number, number], title: 'Sprung, quiet deck',
    text: '12 sinuous steel springs on lined clips under a felt deck. Turn on Inside view to see them.' },
  { id: 'leg', pos: [0.87, 0.06, 0.31] as [number, number, number], title: 'Solid wood legs',
    text: '80 mm turned legs on felt glides, bolted into hardwood blocks. Four finishes.' },
];

export type SceneKey = 'studio' | 'living' | 'evening';
export const SCENES: Record<SceneKey, { label: string; blurb: string; bg: string }> = {
  studio: { label: 'Studio', blurb: 'Clean backdrop, soft studio light', bg: '#cfcac3' },
  living: { label: 'Living room', blurb: 'Oak floor, panelled wall, daylight', bg: '#d6d0c6' },
  evening: { label: 'Evening', blurb: 'Warm lamp light at dusk', bg: '#c9bcab' },
};

export const RESOLUTIONS = [
  { label: 'HD', w: 1920, h: 1080 },
  { label: '2K', w: 2560, h: 1440 },
  { label: '4K', w: 3840, h: 2160 },
  { label: 'Square', w: 2400, h: 2400 },
  { label: 'Portrait', w: 1800, h: 2400 },
];

export interface Config {
  fabric: FabricKey;
  colour: string;      // hex, shell + base
  colourName: string;
  cushion: string | null;   // hex for seat + back cushions, null = match
  cushionName: string;
  leg: string;         // hex
  legName: string;
  pillows: boolean;
  backdrop: string;
  scene: SceneKey;
}

export const DEFAULT_CONFIG: Config = {
  fabric: 'boucle', colour: '#9a5a26', colourName: 'Caramel', cushion: null, cushionName: 'Match',
  leg: '#c79c6c', legName: 'Natural oak', pillows: false, backdrop: '#cfcac3', scene: 'studio',
};
