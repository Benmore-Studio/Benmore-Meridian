# Performance Patterns Reference

## Table of Contents
- [Render Loop Optimization](#render-loop-optimization)
- [Geometry Optimization](#geometry-optimization)
- [Texture Optimization](#texture-optimization)
- [Lighting and Shadows](#lighting-and-shadows)
- [Mobile GPU Strategies](#mobile-gpu-strategies)
- [Bundle Size Optimization](#bundle-size-optimization)
- [Memory Management](#memory-management)
- [Performance Monitoring](#performance-monitoring)

---

## Render Loop Optimization

### Render on Demand (Static Scenes)

For product viewers and configurators that are static between interactions:

```typescript
let needsRender = true;

function requestRender() {
  needsRender = true;
}

function animate() {
  requestAnimationFrame(animate);
  if (!needsRender) return;
  renderer.render(scene, camera);
  needsRender = false;
}

// Trigger re-render on:
controls.addEventListener('change', requestRender);
// state changes, window resize, animation frames
```

**Impact:** 90%+ GPU savings for static scenes.

### Throttled Render Loop (Ambient Animations)

For hero scenes with slow ambient motion:

```typescript
const TARGET_FPS = 30;
const FRAME_DURATION = 1000 / TARGET_FPS;
let lastFrameTime = 0;

function animate(time: number) {
  requestAnimationFrame(animate);
  if (time - lastFrameTime < FRAME_DURATION) return;
  lastFrameTime = time;
  renderer.render(scene, camera);
}
```

### Adaptive Resolution

Scale render resolution based on GPU load:

```typescript
function adaptivePixelRatio(renderer: THREE.WebGLRenderer) {
  const maxDPR = Math.min(window.devicePixelRatio, 2);
  let currentDPR = maxDPR;

  // Measure frame times
  let frameTimes: number[] = [];
  let lastTime = performance.now();

  function checkPerformance() {
    const now = performance.now();
    frameTimes.push(now - lastTime);
    lastTime = now;

    if (frameTimes.length >= 60) {
      const avgFrame = frameTimes.reduce((a, b) => a + b) / frameTimes.length;
      frameTimes = [];

      if (avgFrame > 20 && currentDPR > 1) {        // below 50fps
        currentDPR = Math.max(1, currentDPR - 0.25);
        renderer.setPixelRatio(currentDPR);
      } else if (avgFrame < 12 && currentDPR < maxDPR) {  // above 83fps
        currentDPR = Math.min(maxDPR, currentDPR + 0.25);
        renderer.setPixelRatio(currentDPR);
      }
    }
  }

  return { checkPerformance };
}
```

---

## Geometry Optimization

### Mesh Instancing

For repeated geometry (trees, particles, grid items):

```typescript
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshStandardMaterial({ color: 0x888888 });
const mesh = new THREE.InstancedMesh(geometry, material, COUNT);

const matrix = new THREE.Matrix4();
for (let i = 0; i < COUNT; i++) {
  matrix.setPosition(positions[i].x, positions[i].y, positions[i].z);
  mesh.setMatrixAt(i, matrix);
}
mesh.instanceMatrix.needsUpdate = true;
```

**Impact:** 1000 objects → 1 draw call instead of 1000.

### Level of Detail (LOD)

Switch geometry complexity based on camera distance:

```typescript
const lod = new THREE.LOD();
lod.addLevel(highDetailMesh, 0);      // 0–10 units
lod.addLevel(medDetailMesh, 10);      // 10–50 units
lod.addLevel(lowDetailMesh, 50);      // 50+ units
scene.add(lod);
```

### Geometry Merging

For static scenes with many unique meshes sharing a material:

```typescript
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils';

const geometries = meshes.map(m => {
  const geo = m.geometry.clone();
  geo.applyMatrix4(m.matrixWorld);
  return geo;
});
const merged = mergeGeometries(geometries);
const mergedMesh = new THREE.Mesh(merged, sharedMaterial);
```

**Impact:** Reduces draw calls proportional to mesh count.

---

## Texture Optimization

### Compressed Textures (KTX2 / Basis)

```typescript
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader';

const ktx2Loader = new KTX2Loader()
  .setTranscoderPath('/basis/')       // path to basis_transcoder.wasm
  .detectSupport(renderer);

ktx2Loader.load('texture.ktx2', texture => {
  material.map = texture;
  material.needsUpdate = true;
});
```

**Impact:** 4–6x smaller than PNG, GPU-native decompression.

### Texture Size Guidelines

| Use Case | Max Resolution | Format |
|----------|---------------|--------|
| Albedo/diffuse (hero) | 2048x2048 | KTX2 or WebP |
| Albedo/diffuse (mobile) | 1024x1024 | KTX2 |
| Normal map | 1024x1024 | KTX2 |
| Roughness/metalness | 512x512 | KTX2 (single channel) |
| Environment map | 512x512 per face | HDR → PMREM |
| Shadow map | 512–1024 | Built-in |

### Texture Atlasing

Combine multiple small textures into one atlas to reduce texture bind calls:

```typescript
// Use UV offsets per mesh to sample from atlas regions
material.map.offset.set(0.5, 0);    // sample right half
material.map.repeat.set(0.5, 1);    // half width
```

---

## Lighting and Shadows

### Shadow Optimization

```typescript
// Tighten shadow camera frustum to scene bounds
const light = new THREE.DirectionalLight(0xffffff, 1);
light.castShadow = true;
light.shadow.mapSize.set(1024, 1024);       // 512 for mobile
light.shadow.camera.near = 0.5;
light.shadow.camera.far = 50;
light.shadow.camera.left = -10;
light.shadow.camera.right = 10;
light.shadow.camera.top = 10;
light.shadow.camera.bottom = -10;
light.shadow.bias = -0.0001;                // prevent shadow acne
light.shadow.normalBias = 0.02;

// Contact shadows (cheaper alternative)
// Use @react-three/drei <ContactShadows> or baked shadow planes
```

### Baked Lighting

For static scenes, bake lighting in Blender and export as lightmap textures. No runtime shadow computation needed.

### Light Count Budget

| Platform | Max Lights | Shadow-Casting Lights |
|----------|-----------|----------------------|
| Desktop | 4–8 | 1–2 |
| Mobile | 2–3 | 0–1 |
| Low-end mobile | 1–2 | 0 |

---

## Mobile GPU Strategies

### Device Tier Detection

```typescript
function getDeviceTier(): 'high' | 'mid' | 'low' {
  const gl = document.createElement('canvas').getContext('webgl2') ||
             document.createElement('canvas').getContext('webgl');
  if (!gl) return 'low';

  const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
  const gpuRenderer = debugInfo
    ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
    : '';

  // Known low-end GPUs
  if (/Mali-4|Adreno 3|PowerVR SGX/i.test(gpuRenderer)) return 'low';
  if (/Mali-G[567]|Adreno [456]/i.test(gpuRenderer)) return 'mid';
  return 'high';
}
```

### Tier-Based Settings

```typescript
const SETTINGS = {
  high: { dpr: 2, shadows: true, shadowSize: 1024, antialias: true, postprocessing: true },
  mid:  { dpr: 1.5, shadows: true, shadowSize: 512, antialias: true, postprocessing: false },
  low:  { dpr: 1, shadows: false, shadowSize: 0, antialias: false, postprocessing: false },
};

function applySettings(renderer: THREE.WebGLRenderer, tier: string) {
  const s = SETTINGS[tier];
  renderer.setPixelRatio(s.dpr);
  renderer.shadowMap.enabled = s.shadows;
  if (s.shadows) {
    renderer.shadowMap.type = tier === 'high'
      ? THREE.PCFSoftShadowMap
      : THREE.BasicShadowMap;
  }
}
```

### Mobile-Specific Rules

- Clamp `devicePixelRatio` to max 2 (desktop), max 1.5 (mobile)
- Prefer `MeshLambertMaterial` over `MeshStandardMaterial` on low-end
- Disable post-processing on mobile unless explicitly required
- Use `powerPreference: 'high-performance'` in WebGLRenderer
- Avoid real-time shadows on low-end — use baked or contact shadows
- Reduce geometry: aim for < 100K triangles on mobile scenes

---

## Bundle Size Optimization

### Tree-Shaking Three.js

```typescript
// ✅ GOOD — import only what you need
import { Scene, PerspectiveCamera, WebGLRenderer, Mesh } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

// ❌ BAD — imports everything (~600KB)
import * as THREE from 'three';
```

**Note:** Tree-shaking `three` requires modern bundlers (Vite, webpack 5+) with proper config. Test actual bundle size.

### Code Splitting

```typescript
// Lazy-load Three.js only when the 3D section is visible
const ThreeScene = dynamic(() => import('./ThreeScene'), {
  ssr: false,
  loading: () => <div className="scene-placeholder" />,
});
```

### Size Budget

| Component | Target |
|-----------|--------|
| Three.js core (tree-shaken) | ~150KB gzipped |
| GLTF model (typical product) | 500KB–2MB |
| Environment HDR (compressed) | 200KB–500KB |
| Draco decoder WASM | ~40KB |
| Total 3D bundle | < 3MB on first load |

---

## Memory Management

### Disposal Pattern

```typescript
function disposeScene(scene: THREE.Scene) {
  scene.traverse(object => {
    if (object instanceof THREE.Mesh) {
      object.geometry.dispose();
      if (Array.isArray(object.material)) {
        object.material.forEach(disposeMaterial);
      } else {
        disposeMaterial(object.material);
      }
    }
  });
}

function disposeMaterial(material: THREE.Material) {
  for (const value of Object.values(material)) {
    if (value instanceof THREE.Texture) {
      value.dispose();
    }
  }
  material.dispose();
}
```

### React Cleanup

```typescript
useEffect(() => {
  // setup...
  return () => {
    disposeScene(scene);
    renderer.dispose();
    renderer.forceContextLoss();     // release WebGL context
  };
}, []);
```

---

## Performance Monitoring

### Built-in Stats

```typescript
import Stats from 'three/examples/jsm/libs/stats.module';

const stats = new Stats();
document.body.appendChild(stats.dom);

function animate() {
  stats.begin();
  renderer.render(scene, camera);
  stats.end();
  requestAnimationFrame(animate);
}
```

### Renderer Info

```typescript
// Log after first render to check draw calls and triangles
console.log('Draw calls:', renderer.info.render.calls);
console.log('Triangles:', renderer.info.render.triangles);
console.log('Textures:', renderer.info.memory.textures);
console.log('Geometries:', renderer.info.memory.geometries);
```

### Performance Targets

| Metric | Desktop | Mobile |
|--------|---------|--------|
| FPS | 60 | 30–60 |
| Draw calls | < 100 | < 50 |
| Triangles | < 500K | < 100K |
| Texture memory | < 256MB | < 64MB |
| First paint | < 2s | < 3s |
