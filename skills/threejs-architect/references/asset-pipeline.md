# Asset Pipeline Reference

## Table of Contents
- [Format Selection](#format-selection)
- [Model Optimization](#model-optimization)
- [Draco Compression](#draco-compression)
- [Texture Pipeline](#texture-pipeline)
- [Loading Patterns](#loading-patterns)
- [Caching Strategies](#caching-strategies)

---

## Format Selection

### Preferred: GLB (Binary glTF)

Single-file binary container. Preferred for all web delivery.

| Format | Use When |
|--------|----------|
| `.glb` | Default for everything — single file, binary, fastest to load |
| `.gltf` + separate files | When textures need individual caching or CDN serving |
| `.fbx` | Source format only — convert to GLB before web delivery |
| `.obj` | Legacy — convert to GLB. No animation, no PBR materials |
| `.usdz` | iOS AR Quick Look only — not for Three.js |

### Conversion Pipeline

**From Blender:**
```
File → Export → glTF 2.0 (.glb/.gltf)
  Format: glTF Binary (.glb)
  Include: Selected Objects (or all)
  Transform: +Y Up
  Geometry:
    Apply Modifiers: ✓
    UVs: ✓
    Normals: ✓
    Tangents: ✓ (if using normal maps)
    Vertex Colors: ✓ (if used)
  Animation:
    Export Animations: ✓ (if applicable)
    Shape Keys: ✓ (if used)
  Compression:
    Draco: ✓ (compression level 6)
```

**From FBX/OBJ (CLI):**
```bash
# Using gltf-pipeline
npx gltf-pipeline -i model.fbx -o model.glb --draco.compressionLevel 7

# Using gltf-transform (recommended)
npx gltf-transform optimize input.glb output.glb --compress draco --texture-compress webp
```

**Programmatic with gltf-transform:**
```bash
npm install @gltf-transform/core @gltf-transform/extensions @gltf-transform/functions
```

```typescript
import { NodeIO } from '@gltf-transform/core';
import { dedup, draco, textureCompress, weld, simplify } from '@gltf-transform/functions';
import { KHRONOS_EXTENSIONS } from '@gltf-transform/extensions';
import draco3d from 'draco3dgltf';

const io = new NodeIO()
  .registerExtensions(KHRONOS_EXTENSIONS)
  .registerDependencies({ 'draco3d.decoder': await draco3d.createDecoderModule() });

const doc = await io.read('input.glb');

await doc.transform(
  dedup(),                                    // remove duplicate accessors
  weld({ tolerance: 0.001 }),                  // merge close vertices
  simplify({ ratio: 0.5, error: 0.01 }),       // reduce polygons by 50%
  textureCompress({ encoder: sharp, targetFormat: 'webp' }),
  draco({ compressionLevel: 7 }),              // geometry compression
);

await io.write('output.glb', doc);
```

---

## Model Optimization

### Polygon Budget

| Scene Type | Desktop Budget | Mobile Budget |
|------------|---------------|---------------|
| Single product viewer | 50K–200K tris | 20K–50K tris |
| Configurator (all variants) | 100K–300K tris | 50K–100K tris |
| Hero scene | 50K–150K tris | 20K–50K tris |
| Architecture viz | 200K–500K tris | 50K–150K tris |
| Data viz (instanced) | 10K base × N instances | 5K base × N instances |

### Optimization Checklist

1. **Remove hidden geometry** — backfaces of walls, undersides of objects, interior faces
2. **Decimate** — reduce polygon count by 30–50% where detail loss is imperceptible
3. **Merge meshes** — combine static objects sharing materials to reduce draw calls
4. **Remove unused materials** — delete materials not assigned to any mesh
5. **Clean UV maps** — pack UVs efficiently, remove overlapping
6. **Check normals** — ensure consistent winding order, recalculate if needed
7. **Apply transforms** — freeze position/rotation/scale in modeling tool before export
8. **Single-sided materials** — use `side: THREE.FrontSide` (default) unless transparency requires `DoubleSide`

### Simplification with gltf-transform

```bash
# Reduce to 50% of original triangle count with 1% error tolerance
npx gltf-transform simplify input.glb output.glb --ratio 0.5 --error 0.01
```

---

## Draco Compression

### Setup

Draco decoder must be available at runtime. Three options:

**Option 1: CDN (simplest)**
```typescript
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
```

**Option 2: Self-hosted**
```bash
# Copy decoder files to public directory
cp node_modules/three/examples/jsm/libs/draco/ public/draco/
```
```typescript
dracoLoader.setDecoderPath('/draco/');
```

**Option 3: Bundled WASM**
```typescript
dracoLoader.setDecoderConfig({ type: 'wasm' });
dracoLoader.preload();  // start loading decoder early
```

### With GLTFLoader

```typescript
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('/draco/');

const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);

gltfLoader.load('model.glb', gltf => {
  scene.add(gltf.scene);
});
```

### Compression Impact

| Content | Uncompressed | Draco Level 7 | Reduction |
|---------|-------------|---------------|-----------|
| Simple product (10K tris) | 500KB | 80KB | 84% |
| Detailed product (100K tris) | 5MB | 600KB | 88% |
| Architecture scene (500K tris) | 25MB | 2.5MB | 90% |

---

## Texture Pipeline

### Format Priority

1. **KTX2 + Basis Universal** — best compression, GPU-native, smallest files
2. **WebP** — good compression, wide support, but not GPU-native
3. **JPEG** — fallback for maximum compatibility
4. **PNG** — only when alpha channel is needed

### KTX2 Texture Compression

```bash
# Using gltf-transform
npx gltf-transform ktx input.glb output.glb --slots "baseColor,normal,emissive"

# Using toktx directly
toktx --t2 --encode basis-lz --clevel 2 output.ktx2 input.png
```

### Loading KTX2 in Three.js

```typescript
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader';

const ktx2Loader = new KTX2Loader()
  .setTranscoderPath('/basis/')
  .detectSupport(renderer);

// With GLTFLoader (automatic if model uses KHR_texture_basisu)
gltfLoader.setKTX2Loader(ktx2Loader);
```

### Texture Size Rules

- Power-of-two dimensions (512, 1024, 2048) — required for mipmaps
- Max 2048x2048 for albedo on desktop, 1024x1024 on mobile
- Max 1024x1024 for normal maps
- Max 512x512 for roughness/metalness/AO (often combined into single ORM texture)
- Generate mipmaps: `texture.generateMipmaps = true` (default)

---

## Loading Patterns

### Progressive Loading

Load low-quality placeholder first, swap to high-quality when ready:

```typescript
async function progressiveLoad(scene: THREE.Scene, modelUrl: string) {
  // Phase 1: Load low-poly placeholder (< 50KB)
  const lowPoly = await loadModel(modelUrl.replace('.glb', '-low.glb'));
  scene.add(lowPoly);

  // Phase 2: Load full model in background
  const highPoly = await loadModel(modelUrl);
  scene.remove(lowPoly);
  disposeMesh(lowPoly);
  scene.add(highPoly);
}
```

### Loading Manager

Track progress across multiple assets:

```typescript
const manager = new THREE.LoadingManager();
manager.onProgress = (url, loaded, total) => {
  const progress = (loaded / total) * 100;
  updateLoadingBar(progress);
};
manager.onLoad = () => {
  hideLoadingScreen();
};
manager.onError = (url) => {
  console.error('Failed to load:', url);
  showFallback();
};

const gltfLoader = new GLTFLoader(manager);
const textureLoader = new THREE.TextureLoader(manager);
```

### Preloading

Start loading assets before the 3D section is visible:

```typescript
// Preload model when user scrolls near the section
const preloadObserver = new IntersectionObserver(entries => {
  if (entries[0].isIntersecting) {
    preloadObserver.disconnect();
    gltfLoader.load('model.glb', gltf => {
      cachedModel = gltf;
    });
  }
}, { rootMargin: '500px' });  // trigger 500px before visible
preloadObserver.observe(sectionElement);
```

---

## Caching Strategies

### Three.js Cache

```typescript
THREE.Cache.enabled = true;  // enables in-memory caching of loaded files
```

### Service Worker Caching

For repeat visitors, cache 3D assets with a service worker:

```typescript
// In service worker
const CACHE_NAME = 'three-assets-v1';
const ASSET_URLS = ['/models/product.glb', '/textures/env.hdr', '/draco/draco_decoder.wasm'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSET_URLS)));
});

self.addEventListener('fetch', event => {
  if (event.request.url.match(/\.(glb|hdr|ktx2|wasm)$/)) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
  }
});
```

### CDN Headers

```
Cache-Control: public, max-age=31536000, immutable
```

Use content hashing in filenames (`model.a1b2c3.glb`) for cache busting.
