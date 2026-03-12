# Scene Templates Reference

## Table of Contents
- [Template System Overview](#template-system-overview)
- [Product Configurator Template](#product-configurator-template)
- [Scroll Animation Template](#scroll-animation-template)
- [Product Viewer Template](#product-viewer-template)
- [Hero Marketing Template](#hero-marketing-template)
- [Architecture Visualizer Template](#architecture-visualizer-template)
- [Data Visualization Template](#data-visualization-template)

---

## Template System Overview

Templates are reusable scene architectures for common project types. Each template defines:

- Scene graph structure
- Camera system
- Lighting setup
- Interaction model
- Animation system
- Performance constraints
- File structure

Select the template matching the detected scene type (see SKILL.md Scene Type Detection table), then adapt to the specific project.

---

## Product Configurator Template

**Use when:** Users select options (materials, parts, colors) that update a 3D model in real time.

### Scene Graph

```
Scene
├── ModelGroup
│   ├── BaseMesh (always visible)
│   ├── PartGroup_A
│   │   ├── Option_A1 (visible when selected)
│   │   ├── Option_A2
│   │   └── Option_A3
│   └── PartGroup_B
│       ├── Option_B1
│       └── Option_B2
├── Environment
│   ├── GroundPlane / ContactShadow
│   └── EnvironmentMap (HDR)
└── Lights
    ├── AmbientLight (0.3 intensity)
    ├── DirectionalLight (1.0, shadows)
    └── FillLight (0.2, no shadows)
```

### State Architecture

```typescript
// Pure configuration state — no Three.js types
interface ConfigState {
  parts: Record<string, string>;      // partGroupName → selectedOptionName
  materials: Record<string, string>;  // meshName → materialPresetId
  colors: Record<string, string>;     // meshName → hex color
  camera: 'overview' | 'detail-a' | 'detail-b';
}

// Camera presets for smooth transitions
const CAMERA_PRESETS = {
  overview: { position: [3, 2, 3], target: [0, 0.5, 0], fov: 45 },
  'detail-a': { position: [1, 1, 1.5], target: [0, 0.8, 0], fov: 35 },
  'detail-b': { position: [-1, 0.5, 2], target: [0, 0.3, 0], fov: 40 },
};
```

### File Structure

```
configurator/
├── ConfiguratorScene.tsx       — canvas, scene setup, state subscription
├── useConfigState.ts           — Zustand store for selections
├── OptionPanel.tsx             — UI controls (no three imports)
├── materials/
│   ├── presets.ts              — material definitions (color, roughness, metalness)
│   └── materialFactory.ts     — create THREE materials from presets
├── cameraController.ts         — animated camera transitions
└── modelLoader.ts              — GLTF + Draco loading with progress
```

### Performance Rules
- Pre-create all material variants at load time
- Swap `.visible` for geometry options (never add/remove from scene)
- Use render-on-demand (re-render only on state change or camera move)
- Cache loaded models: `THREE.Cache.enabled = true`

---

## Scroll Animation Template

**Use when:** Camera, objects, or lighting animate as the user scrolls through page sections.

### Scene Graph

```
Scene
├── CameraRig (empty group — animate this, camera is child)
│   └── PerspectiveCamera
├── ScrollObjects
│   ├── Object_Section1
│   ├── Object_Section2
│   └── Object_Section3
├── Environment
│   └── Background (gradient or skybox)
└── Lights
    ├── AmbientLight
    └── DirectionalLight (animated intensity per section)
```

### Scroll Architecture

```typescript
interface ScrollSection {
  id: string;
  startProgress: number;   // 0–1
  endProgress: number;     // 0–1
  camera: { position: [number, number, number]; lookAt: [number, number, number] };
  objects: Array<{
    name: string;
    rotation?: [number, number, number];
    position?: [number, number, number];
    opacity?: number;
    scale?: number;
  }>;
  light?: { intensity: number; color: string };
}

const SECTIONS: ScrollSection[] = [
  {
    id: 'intro',
    startProgress: 0,
    endProgress: 0.3,
    camera: { position: [0, 2, 8], lookAt: [0, 0, 0] },
    objects: [{ name: 'hero-object', rotation: [0, Math.PI * 2, 0] }],
  },
  // ... more sections
];
```

### File Structure

```
scroll-scene/
├── ScrollScene.tsx           — fixed canvas + scroll container
├── useScrollTimeline.ts      — GSAP ScrollTrigger setup
├── sections.ts               — keyframe data per scroll section
├── sceneSetup.ts             — model loading + scene graph
└── parallax.ts               — depth-based parallax helpers
```

### Layout Pattern

```tsx
// The canvas is fixed, content scrolls over it
<div className="scroll-container" style={{ height: '400vh' }}>
  <canvas style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: -1 }} />
  <section className="scroll-section" style={{ height: '100vh' }}>
    <h2>Section 1 content overlays the 3D scene</h2>
  </section>
  <section className="scroll-section" style={{ height: '100vh' }}>
    <h2>Section 2</h2>
  </section>
</div>
```

### Performance Rules
- Only one render driver: either `requestAnimationFrame` or GSAP scrub — never both
- Kill all ScrollTrigger instances on unmount
- `scrub: 1` for smooth interpolation (not `scrub: true`)
- Reduce polygon count aggressively — scroll scenes share GPU with page rendering

---

## Product Viewer Template

**Use when:** Users orbit, zoom, and inspect a single 3D model.

### Scene Graph

```
Scene
├── ModelGroup
│   └── LoadedModel (centered at origin)
├── Environment
│   ├── EnvironmentMap (HDR preset: studio, warehouse, sunset)
│   └── ContactShadow (or GroundPlane with receiveShadow)
├── Lights
│   ├── AmbientLight (0.2)
│   └── DirectionalLight (1.0, shadows)
└── Annotations (optional)
    ├── Hotspot_1 (Sprite + raycaster)
    └── Hotspot_2
```

### File Structure

```
product-viewer/
├── ProductViewer.tsx          — canvas + controls + environment
├── useModelLoader.ts          — GLTF loading + center/scale on load
├── Annotations.tsx            — clickable hotspot overlays
├── environment.ts             — HDR loading + tone mapping config
└── viewerControls.ts          — OrbitControls config + limits
```

### Camera Auto-Fit

```typescript
function fitCameraToModel(camera: THREE.PerspectiveCamera, model: THREE.Object3D, controls: OrbitControls) {
  const box = new THREE.Box3().setFromObject(model);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = camera.fov * (Math.PI / 180);
  const distance = maxDim / (2 * Math.tan(fov / 2)) * 1.5;

  camera.position.set(center.x + distance * 0.5, center.y + distance * 0.3, center.z + distance);
  controls.target.copy(center);
  controls.update();
}
```

### Performance Rules
- **Always** render on demand — re-render only on controls change
- Use `OrbitControls.enableDamping = true` with `dampingFactor: 0.05`
- Limit zoom: `controls.minDistance`, `controls.maxDistance`
- Limit vertical rotation: `controls.maxPolarAngle = Math.PI / 2` (prevent seeing bottom)

---

## Hero Marketing Template

**Use when:** Ambient 3D animation as a visual centerpiece on a landing page.

### Scene Graph

```
Scene
├── HeroObjects
│   ├── PrimaryObject (animated rotation/float)
│   └── ParticleSystem (optional ambient particles)
├── Environment
│   └── Background (transparent — composites over page CSS)
└── Lights
    ├── AmbientLight (0.4)
    ├── KeyLight (directional, animated color)
    └── RimLight (from behind, accent color)
```

### File Structure

```
hero-scene/
├── HeroScene.tsx              — lazy-initialized canvas
├── useHeroAnimation.ts        — ambient animation loop
├── particles.ts               — optional particle system
└── heroConfig.ts              — animation speed, colors, camera position
```

### Lazy Initialization

```typescript
// Only initialize Three.js when canvas enters viewport
function HeroScene() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); observer.disconnect(); } },
      { threshold: 0.1 }
    );
    if (canvasRef.current) observer.observe(canvasRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible || !canvasRef.current) return;
    // Initialize Three.js scene here
  }, [visible]);

  return <canvas ref={canvasRef} />;
}
```

### Performance Rules
- Lazy-init: never block page load
- Pixel ratio clamped to 1.5
- Pause animation when tab is hidden (`document.visibilitychange`)
- `alpha: true` — composite over page, no opaque background
- Total model size < 2MB
- Provide CSS gradient fallback while loading

---

## Architecture Visualizer Template

**Use when:** Rendering buildings, floor plans, or construction models.

### Scene Graph

```
Scene
├── BuildingModel
│   ├── Exterior
│   ├── Interior
│   │   ├── Floor_1
│   │   ├── Floor_2
│   │   └── Floor_3
│   └── Surroundings (landscape, roads)
├── ClippingPlanes (for section cuts)
├── Measurements (line geometries + labels)
├── Environment
│   ├── Sky (Hemisphere light or sky shader)
│   └── Ground (large plane, shadow receiver)
└── Lights
    ├── HemisphereLight (sky + ground colors)
    ├── DirectionalLight (sun, shadows)
    └── AmbientLight (0.2 fill)
```

### File Structure

```
arch-viz/
├── ArchScene.tsx               — canvas + model + controls
├── useFloorSelector.ts         — floor isolation toggle
├── sectionPlane.ts             — THREE.Plane-based section cuts
├── measurements.ts             — line geometry + CSS2D labels
├── sunPosition.ts              — directional light from sun angle
└── archModelLoader.ts          — multi-part GLTF loading
```

### Performance Rules
- Use LOD for distant buildings
- Merge static meshes per material
- Section planes via `material.clippingPlanes` (not geometry slicing)
- Limit shadow map to building footprint

---

## Data Visualization Template

**Use when:** 3D charts, spatial data, or instanced data points.

### Scene Graph

```
Scene
├── DataLayer
│   ├── InstancedMesh (data points)
│   ├── BarGeometry (instanced boxes)
│   └── ConnectionLines (BufferGeometry)
├── Axes (optional)
│   ├── X_Axis (line + labels)
│   ├── Y_Axis
│   └── Z_Axis
├── Tooltip (CSS2DObject, positioned on hover)
└── Lights
    ├── AmbientLight (0.5)
    └── DirectionalLight (0.8)
```

### File Structure

```
data-viz/
├── DataVizScene.tsx            — canvas + camera + controls
├── useDataPoints.ts            — transform data → instance matrices + colors
├── axes.ts                     — axis lines + tick labels
├── tooltip.ts                  — CSS2DRenderer hover tooltip
└── colorScale.ts               — value → color mapping (d3-scale compatible)
```

### Performance Rules
- Always use `InstancedMesh` for data points (never individual meshes)
- Update `instanceMatrix` and `instanceColor` in batch, call `.needsUpdate = true` once
- For > 100K points, use `THREE.Points` with custom shader material
- Render on demand — re-render only when data or camera changes
