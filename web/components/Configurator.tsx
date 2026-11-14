'use client';
import dynamic from 'next/dynamic';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  BACKDROPS, Config, DEFAULT_CONFIG, FABRICS, FabricKey, HOTSPOTS, LEGS, RESOLUTIONS, SCENES, SceneKey, VIEWS,
} from '../lib/options';
import type { RenderFn } from './Scene';

const SAMPLES = [
  { label: 'Draft', n: 96 },
  { label: 'High', n: 320 },
  { label: 'Ultra', n: 1000 },
];
const fmt = (s: number) => (s < 60 ? `${Math.round(s)} s` : `${Math.floor(s / 60)} min ${Math.round(s % 60)} s`);

const Scene = dynamic(() => import('./Scene'), { ssr: false, loading: () => <div className="canvas-wait">Preparing 3D view…</div> });

function readUrl(): Partial<Config> {
  if (typeof window === 'undefined') return {};
  const q = new URLSearchParams(window.location.search);
  const out: Partial<Config> = {};
  const f = q.get('fabric') as FabricKey | null;
  if (f && FABRICS[f]) out.fabric = f;
  const fab = FABRICS[out.fabric ?? 'boucle'];
  const name = (hex: string) => fab.colours.find((s) => s.hex.toLowerCase() === hex.toLowerCase())?.name ?? 'Custom';
  const c = q.get('colour');
  if (c && /^[0-9a-f]{6}$/i.test(c)) { out.colour = '#' + c; out.colourName = name(out.colour); }
  const cu = q.get('cushion');
  if (cu && /^[0-9a-f]{6}$/i.test(cu)) { out.cushion = '#' + cu; out.cushionName = name(out.cushion); }
  const l = LEGS.find((s) => s.name === q.get('legs'));
  if (l) { out.leg = l.hex; out.legName = l.name; }
  if (q.get('pillows') === '1') out.pillows = true;
  const sc = q.get('scene') as SceneKey | null;
  if (sc && SCENES[sc]) out.scene = sc;
  return out;
}

const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-');

export default function Configurator() {
  const [cfg, setCfg] = useState<Config>(DEFAULT_CONFIG);
  const [xray, setXray] = useState(false);
  const [dims, setDims] = useState(false);
  const [hotspots, setHotspots] = useState(true);
  const [autoRotate, setAutoRotate] = useState(true);
  const [view, setView] = useState({ name: 'hero', n: 0 });
  const [active, setActive] = useState<string | null>(null);
  const [copied, setCopied] = useState('');
  const [studio, setStudio] = useState(false);
  const [panelOpen, setPanelOpen] = useState(true);
  const [res, setRes] = useState(1);
  const [busy, setBusy] = useState(false);
  const [shot, setShot] = useState<{ url: string; w: number; h: number; pt: boolean; s: number } | null>(null);
  const [quality, setQuality] = useState<'photoreal' | 'fast'>('photoreal');
  const [sIdx, setSIdx] = useState(1);
  const [denoise, setDenoise] = useState(true);
  const [prog, setProg] = useState<{ s: number; total: number; t0: number } | null>(null);
  const stopRef = useRef<'finish' | 'cancel' | null>(null);
  const previewHost = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const renderRef = useRef<RenderFn | null>(null);
  const registerRender = useCallback((fn: RenderFn) => { renderRef.current = fn; }, []);

  useEffect(() => {
    setCfg((c) => ({ ...c, ...readUrl() }));
    const q = new URLSearchParams(window.location.search);
    const v = q.get('view');
    if (v && VIEWS[v]) setView({ name: v, n: 0 });
    if (q.get('spin') === '0' || v) setAutoRotate(false);
    if (q.get('xray') === '1') setXray(true);
    if (q.get('panel') === '0') setPanelOpen(false);
    const tr = q.get('testrender');   // test hook: ?testrender=pt (small path-traced) or ?testrender=1 (fast HD)
    if (tr) setTimeout(() => {
      setStudio(true);
      setTimeout(() => doRenderRef.current?.(tr === 'pt' ? { w: 240, h: 150, samples: 6, photoreal: true }
        : { w: 1920, h: 1080, samples: 1, photoreal: false }), 300);
    }, 6000);
  }, []);
  useEffect(() => {
    const q = new URLSearchParams({
      fabric: cfg.fabric, colour: cfg.colour.slice(1), legs: cfg.legName, pillows: cfg.pillows ? '1' : '0', scene: cfg.scene,
    });
    if (cfg.cushion) q.set('cushion', cfg.cushion.slice(1));
    window.history.replaceState(null, '', `?${q.toString()}`);
  }, [cfg]);

  const fabric = FABRICS[cfg.fabric];
  const pickFabric = (k: FabricKey) => {
    const f = FABRICS[k];
    setCfg((c) => ({ ...c, fabric: k, colour: f.colours[0].hex, colourName: f.colours[0].name, cushion: null, cushionName: 'Match' }));
  };
  const go = (name: string) => { setAutoRotate(false); setView((v) => ({ name, n: v.n + 1 })); };
  const stopSpin = useCallback(() => setAutoRotate(false), []);
  const fileBase = `caramel-shell-${cfg.fabric}-${slug(cfg.colourName)}${cfg.cushion ? '-' + slug(cfg.cushionName) : ''}-${cfg.scene}`;

  const quickSave = () => {
    const c = canvasRef.current; if (!c) return;
    const a = document.createElement('a'); a.href = c.toDataURL('image/png'); a.download = `${fileBase}.png`; a.click();
  };
  const copyLink = async () => {
    try { await navigator.clipboard.writeText(window.location.href); setCopied('Link copied'); }
    catch { setCopied('Copy the address bar to share'); }
    setTimeout(() => setCopied(''), 2200);
  };
  const openStudio = () => { setAutoRotate(false); setShot(null); setStudio(true); };
  const doRender = async (override?: { w: number; h: number; samples: number; photoreal: boolean }) => {
    const fn = renderRef.current; if (!fn) return;
    const r = override ?? { ...RESOLUTIONS[res], samples: SAMPLES[sIdx].n, photoreal: quality === 'photoreal' };
    setBusy(true); setShot(null); stopRef.current = null;
    setProg({ s: 0, total: r.samples, t0: Date.now() });
    const prevDims = dims, prevHot = hotspots;
    setDims(false); setHotspots(false); setActive(null);
    await new Promise((ok) => setTimeout(ok, 60));
    let lastS = 0;
    try {
      const url = await fn(r.w, r.h, {
        photoreal: r.photoreal, samples: r.samples, denoise,
        shouldStop: () => stopRef.current,
        onProgress: (s, total, canvas) => {
          lastS = s;
          if (previewHost.current && canvas.parentElement !== previewHost.current) previewHost.current.replaceChildren(canvas);
          setProg((p) => ({ s, total, t0: p?.t0 ?? Date.now() }));
        },
      });
      if (url) setShot({ url, w: r.w, h: r.h, pt: r.photoreal, s: Math.floor(lastS) });
    } catch (e) {
      console.error(e);
      alert('Photoreal rendering is not supported by this browser or graphics card. Try the Fast render.');
    } finally { setDims(prevDims); setHotspots(prevHot); setBusy(false); setProg(null); }
  };
  const doRenderRef = useRef(doRender); doRenderRef.current = doRender;
  const hs = HOTSPOTS.find((h) => h.id === active);
  const ptMode = prog !== null && (quality === 'photoreal' || prog.total > 1);

  return (
    <div className={`app${panelOpen ? '' : ' panel-hidden'}`}>
      <section className="stage" aria-label="3D sofa viewer">
        <Scene
          cfg={cfg} xray={xray} dims={dims} hotspots={hotspots && !xray} autoRotate={autoRotate && !studio}
          view={view} activeHotspot={active} onHotspot={setActive} onUserMove={stopSpin}
          onReady={(c) => { canvasRef.current = c; }} registerRender={registerRender}
        />
        <div className="stage-top">
          <div className="brand">
            <span className="eyebrow">Configure</span>
            <strong>Caramel Shell 2S</strong>
          </div>
          <div className="top-right">
            <div className="views" role="group" aria-label="Camera views">
              {Object.entries(VIEWS).map(([k, v]) => (
                <button key={k} className={`chip-btn${view.name === k ? ' on' : ''}`} onClick={() => go(k)}>{v.label}</button>
              ))}
            </div>
            <button className="panel-toggle" onClick={() => setPanelOpen((o) => !o)} aria-expanded={panelOpen} aria-controls="options-panel"
              title={panelOpen ? 'Hide options' : 'Show options'}>
              <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M15 4v16" />
                <path d={panelOpen ? 'M8 10l2 2-2 2' : 'M11 10l-2 2 2 2'} /></svg>
              {panelOpen ? 'Hide options' : 'Customize'}
            </button>
          </div>
        </div>
        {hs && (
          <div className="hs-card" role="status">
            <button className="hs-x" onClick={() => setActive(null)} aria-label="Close">×</button>
            <strong>{hs.title}</strong>
            <p>{hs.text}</p>
          </div>
        )}
        <div className="stage-bottom">
          <button className="render-cta" onClick={openStudio}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3v11H4z" /><circle cx="12" cy="13" r="3.5" /></svg>
            Render photo
          </button>
          <div className="tools">
            <button className={`tool${autoRotate ? ' on' : ''}`} onClick={() => setAutoRotate((v) => !v)}>Auto-rotate</button>
            <button className={`tool${dims ? ' on' : ''}`} onClick={() => setDims((v) => !v)}>Dimensions</button>
            <button className={`tool${xray ? ' on' : ''}`} onClick={() => { setXray((v) => !v); setActive(null); }}>Inside view</button>
            <button className={`tool${hotspots ? ' on' : ''}`} onClick={() => setHotspots((v) => !v)}>Hotspots</button>
          </div>
        </div>

        {studio && (
          <div className={`studio${busy ? ' busy' : ''}`} role="dialog" aria-modal="false" aria-label="Render photo">
            {busy && (
              <div className="studio-cover">
                {ptMode ? (
                  <div className="pt-live">
                    <div className="pt-preview" ref={previewHost}><div className="spinner" /></div>
                    <div className="pt-bar"><span style={{ width: `${prog ? Math.min(100, (prog.s / prog.total) * 100) : 0}%` }} /></div>
                    <div className="pt-row">
                      <span>
                        {prog && prog.s < 1 ? 'Preparing the scene and compiling the path tracer…'
                          : prog && `Path tracing · ${Math.floor(prog.s)} / ${prog.total} samples · ${fmt((Date.now() - prog.t0) / 1000)}`
                            + (prog.s > 2 ? ` · about ${fmt(((Date.now() - prog.t0) / 1000) * (prog.total - prog.s) / prog.s)} left` : '')}
                      </span>
                      <span className="actions">
                        <button className="btn" onClick={() => { stopRef.current = 'finish'; }}>Finish now</button>
                        <button className="btn ghost" onClick={() => { stopRef.current = 'cancel'; }}>Cancel</button>
                      </span>
                    </div>
                  </div>
                ) : (<><div className="spinner" />Rendering {RESOLUTIONS[res].w} × {RESOLUTIONS[res].h}…</>)}
              </div>
            )}
            {shot && !busy ? (
              <div className="studio-result">
                <img src={shot.url} alt="Rendered photo of your configured sofa" />
                <div className="studio-row">
                  <span className="note">{shot.w} × {shot.h} px · {SCENES[cfg.scene].label} · {shot.pt ? `path traced, ${shot.s} samples` : 'fast render'}</span>
                  <div className="actions">
                    <a className="btn" href={shot.url} download={`${fileBase}-${shot.w}x${shot.h}.jpg`}>Download photo</a>
                    <button className="btn ghost" onClick={() => setShot(null)}>Change set-up</button>
                    <button className="btn ghost" onClick={() => setStudio(false)}>Close</button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="studio-card">
                <div className="studio-head">
                  <div><span className="eyebrow">Photo studio</span><h2>Render a photo of your sofa</h2></div>
                  <button className="hs-x" onClick={() => setStudio(false)} aria-label="Close">×</button>
                </div>
                <p className="note">Frame the shot in the 3D view (drag, zoom, or pick a camera view), choose a setting and a size, then render.</p>
                <div className="group-head"><h3>Setting</h3></div>
                <div className="scene-pick">
                  {(Object.keys(SCENES) as SceneKey[]).map((k) => (
                    <button key={k} className={cfg.scene === k ? 'on' : ''} onClick={() => setCfg((c) => ({ ...c, scene: k }))}>
                      <span className={`scene-thumb ${k}`} />
                      <b>{SCENES[k].label}</b><span>{SCENES[k].blurb}</span>
                    </button>
                  ))}
                </div>
                <div className="group-head"><h3>Quality</h3></div>
                <div className="quality-pick">
                  <button className={quality === 'photoreal' ? 'on' : ''} onClick={() => setQuality('photoreal')}>
                    <b>Photoreal</b><span>Path traced like Blender Cycles: real bounced light, soft shadows, reflections</span>
                  </button>
                  <button className={quality === 'fast' ? 'on' : ''} onClick={() => setQuality('fast')}>
                    <b>Fast</b><span>Instant real-time render for quick previews</span>
                  </button>
                </div>
                {quality === 'photoreal' && (
                  <>
                    <div className="seg three">
                      {SAMPLES.map((s, i) => (
                        <button key={s.label} className={sIdx === i ? 'on' : ''} onClick={() => setSIdx(i)}>{s.label}<small>{s.n} samples</small></button>
                      ))}
                    </div>
                    <label className="toggle">
                      <input id="denoise" type="checkbox" checked={denoise} onChange={(e) => setDenoise(e.target.checked)} />
                      <span className="track"><span /></span>Denoise the final image
                    </label>
                    <p className="note">Render time depends on your graphics card. You can finish early at any time and keep the image.</p>
                  </>
                )}
                <div className="group-head"><h3>Size</h3></div>
                <div className="seg res">
                  {RESOLUTIONS.map((r, i) => (
                    <button key={r.label} className={res === i ? 'on' : ''} onClick={() => setRes(i)}>
                      {r.label}<small>{r.w}×{r.h}</small>
                    </button>
                  ))}
                </div>
                <label className="toggle">
                  <input id="studio-pillows" type="checkbox" checked={cfg.pillows} onChange={(e) => setCfg((c) => ({ ...c, pillows: e.target.checked }))} />
                  <span className="track"><span /></span>Style with scatter cushions
                </label>
                <button id="do-render" className="btn big" onClick={() => doRender()} disabled={busy}>{quality === 'photoreal' ? 'Start photoreal render' : 'Render photo'}</button>
              </div>
            )}
          </div>
        )}
      </section>

      <aside className="panel" id="options-panel" hidden={!panelOpen}>
        <header className="panel-head">
          <p className="eyebrow">Two-seat sofa · 190 × 90 × 78 cm</p>
          <h1>Caramel Shell 2S</h1>
          <p className="muted">A sculpted shell sofa with deep cushions and solid wood legs. Make it yours.</p>
        </header>

        <div className="group">
          <div className="group-head"><h2>Material</h2></div>
          <div className="seg" role="tablist" aria-label="Material">
            {(Object.keys(FABRICS) as FabricKey[]).map((k) => (
              <button key={k} role="tab" aria-selected={cfg.fabric === k} className={cfg.fabric === k ? 'on' : ''} onClick={() => pickFabric(k)}>
                {FABRICS[k].label}
              </button>
            ))}
          </div>
          <p className="note">{fabric.blurb}</p>
        </div>

        <div className="group">
          <div className="group-head"><h2>Colour</h2><span className="value">{cfg.colourName}</span></div>
          <div className="swatches">
            {fabric.colours.map((s) => (
              <button key={s.hex} className={`sw${cfg.colour === s.hex ? ' on' : ''}`} style={{ background: s.hex }}
                title={s.name} aria-label={s.name} aria-pressed={cfg.colour === s.hex}
                onClick={() => setCfg((c) => ({ ...c, colour: s.hex, colourName: s.name }))} />
            ))}
            <label className="sw custom" title="Pick any colour">
              <input id="custom-colour" type="color" value={cfg.colour}
                onChange={(e) => setCfg((c) => ({ ...c, colour: e.target.value, colourName: 'Custom' }))} />
              <span aria-hidden="true">+</span>
            </label>
          </div>
        </div>

        <div className="group">
          <div className="group-head"><h2>Cushion colour</h2><span className="value">{cfg.cushion ? cfg.cushionName : 'Matches the frame'}</span></div>
          <div className="swatches">
            <button className={`sw match${cfg.cushion === null ? ' on' : ''}`} title="Match the frame" aria-label="Match the frame"
              aria-pressed={cfg.cushion === null} style={{ background: cfg.colour }}
              onClick={() => setCfg((c) => ({ ...c, cushion: null, cushionName: 'Match' }))}><span aria-hidden="true">=</span></button>
            {fabric.colours.filter((s) => s.hex !== cfg.colour).map((s) => (
              <button key={s.hex} className={`sw small${cfg.cushion === s.hex ? ' on' : ''}`} style={{ background: s.hex }}
                title={s.name} aria-label={`Cushions in ${s.name}`} aria-pressed={cfg.cushion === s.hex}
                onClick={() => setCfg((c) => ({ ...c, cushion: s.hex, cushionName: s.name }))} />
            ))}
          </div>
          <p className="note">Pick a contrast colour for the seat and back cushions for a two-tone look.</p>
        </div>

        <div className="group">
          <div className="group-head"><h2>Legs</h2><span className="value">{cfg.legName}</span></div>
          <div className="swatches">
            {LEGS.map((s) => (
              <button key={s.hex} className={`sw wood${cfg.leg === s.hex ? ' on' : ''}`} style={{ background: s.hex }}
                title={s.name} aria-label={s.name} aria-pressed={cfg.leg === s.hex}
                onClick={() => setCfg((c) => ({ ...c, leg: s.hex, legName: s.name }))} />
            ))}
          </div>
        </div>

        <div className="group">
          <div className="group-head"><h2>Scatter cushions</h2><span className="value">{cfg.pillows ? 'Added' : 'None'}</span></div>
          <label className="toggle">
            <input id="pillows" type="checkbox" checked={cfg.pillows} onChange={(e) => setCfg((c) => ({ ...c, pillows: e.target.checked }))} />
            <span className="track"><span /></span>
            Grey bouclé, rust velvet and oatmeal linen
          </label>
        </div>

        <div className="group">
          <div className="group-head"><h2>Setting</h2><span className="value">{SCENES[cfg.scene].label}</span></div>
          <div className="seg three">
            {(Object.keys(SCENES) as SceneKey[]).map((k) => (
              <button key={k} className={cfg.scene === k ? 'on' : ''} onClick={() => setCfg((c) => ({ ...c, scene: k }))}>{SCENES[k].label}</button>
            ))}
          </div>
          {cfg.scene === 'studio' && (
            <div className="swatches">
              {BACKDROPS.map((s) => (
                <button key={s.hex} className={`sw small${cfg.backdrop === s.hex ? ' on' : ''}`} style={{ background: s.hex }}
                  title={s.name} aria-label={`Backdrop ${s.name}`} aria-pressed={cfg.backdrop === s.hex}
                  onClick={() => setCfg((c) => ({ ...c, backdrop: s.hex }))} />
              ))}
            </div>
          )}
        </div>

        <div className="summary">
          <div>
            <span className="eyebrow">Your sofa</span>
            <p><strong>{fabric.label} · {cfg.colourName}{cfg.cushion ? ` with ${cfg.cushionName} cushions` : ''}</strong><br />
              {cfg.legName} legs{cfg.pillows ? ' · with scatter cushions' : ''}</p>
          </div>
          <div className="actions">
            <button className="btn" onClick={openStudio}>Render photo</button>
            <button className="btn ghost" onClick={quickSave}>Quick snapshot</button>
            <button className="btn ghost" onClick={copyLink}>Copy link</button>
            <button className="btn ghost" onClick={() => { setCfg(DEFAULT_CONFIG); go('hero'); setXray(false); setDims(false); }}>Reset</button>
          </div>
          {copied && <p className="note" role="status">{copied}</p>}
        </div>

        <dl className="specs">
          <div><dt>Width</dt><dd>190 cm</dd></div>
          <div><dt>Depth</dt><dd>90 cm</dd></div>
          <div><dt>Height</dt><dd>78 cm</dd></div>
          <div><dt>Seat height</dt><dd>44.5 cm</dd></div>
          <div><dt>Seat depth</dt><dd>53 cm</dd></div>
          <div><dt>Weight</dt><dd>≈ 69 kg</dd></div>
        </dl>
      </aside>
    </div>
  );
}
