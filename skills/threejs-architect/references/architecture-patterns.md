# Architecture Patterns Reference

## Table of Contents
- [Configurator Architecture](#configurator-architecture)
- [Scroll Animation Architecture](#scroll-animation-architecture)
- [Product Viewer Architecture](#product-viewer-architecture)
- [Hero Scene Architecture](#hero-scene-architecture)
- [Framework Integration Patterns](#framework-integration-patterns)

---

## Configurator Architecture

**State-driven scene where user selections update materials, meshes, or geometry in real time.**

### Core Pattern

```typescript
// configuratorState.ts — single source of truth
interface ConfiguratorState {
  selectedMaterial: string;
  selectedParts: Record<string, string>;  // partName → optionId
  colorOverrides: Record<string, string>;
  cameraPosition: 'default' | 'detail' | 'overview';
}

// State change → scene update (never mutate scene directly from UI)
function applyState(scene: THREE.Scene, state: ConfiguratorState) {
  for (const [partName, optionId] of Object.entries(state.selectedParts)) {
    const part = scene.getObjectByName(partName);
    if (!part) continue;
    // Swap visibility for geometry options
    part.children.forEach(child => {
      child.visible = child.name === optionId;
    });
  }
  // Apply material overrides
  for (const [meshName, color] of Object.entries(state.colorOverrides)) {
    const mesh = scene.getObjectByName(meshName) as THREE.Mesh;
    if (mesh?.material instanceof THREE.MeshStandardMaterial) {
      mesh.material.color.set(color);
      mesh.material.needsUpdate = true;
    }
  }
}
```

### File Structure

```
configurator/
├── ConfiguratorScene.tsx    — scene setup, model loading, state application
├── useConfiguratorState.ts  — Zustand/Jotai store for option selections
├── OptionPanel.tsx          — UI panel (pure React, no Three.js imports)
├── materials.ts             — material presets and factories
├── modelLoader.ts           — GLTF loader with Draco, caching
└── cameraController.ts      — animated camera transitions between views
```

### Key Rules
- UI components never import `three` — they dispatch state changes only
- Scene reacts to state changes via subscription (useEffect or Zustand subscribe)
- Pre-create all material variants at load time, swap references (don't create on click)
- Use `THREE.Cache.enabled = true` for repeated model loads

---

## Scroll Animation Architecture

**Camera and objects animate based on scroll position using normalized progress values.**

### Core Pattern

```typescript
// scrollController.ts
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
gsap.registerPlugin(ScrollTrigger);

interface ScrollKeyframe {
  progress: number;          // 0–1 normalized scroll position
  cameraPosition: [number, number, number];
  cameraLookAt: [number, number, number];
  objectRotation?: [number, number, number];
  lightIntensity?: number;
}

function createScrollTimeline(
  scene: THREE.Scene,
  camera: THREE.PerspectiveCamera,
  keyframes: ScrollKeyframe[],
  triggerElement: string
) {
  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: triggerElement,
      start: 'top top',
      end: 'bottom bottom',
      scrub: 1,              // smooth scrub
      invalidateOnRefresh: true,
    }
  });

  keyframes.forEach((kf, i) => {
    if (i === 0) return;
    const prev = keyframes[i - 1];
    const duration = kf.progress - prev.progress;

    tl.to(camera.position, {
      x: kf.cameraPosition[0],
      y: kf.cameraPosition[1],
      z: kf.cameraPosition[2],
      duration,
      ease: 'none',
    }, prev.progress);
  });

  return tl;
}
```

### File Structure

```
scroll-scene/
├── ScrollScene.tsx          — canvas + scroll container layout
├── useScrollScene.ts        — Three.js setup + GSAP timeline
├── keyframes.ts             — scroll position → camera/object states
├── sceneObjects.ts          — model loading and scene graph setup
└── parallaxLayers.ts        — depth-based parallax offset helpers
```

### Key Rules
- Canvas must be `position: fixed` with content scrolling over it, OR use ScrollTrigger pin
- Never animate with `requestAnimationFrame` AND ScrollTrigger simultaneously — pick one driver
- Use `scrub: 1` (not `scrub: true`) for smooth interpolation
- Clamp scroll progress to 0–1 to prevent overshoot on bounce-scroll devices
- Kill ScrollTrigger instances on unmount: `ScrollTrigger.getAll().forEach(t => t.kill())`

---

## Product Viewer Architecture

**Orbit-controlled 3D model viewer with optional hotspots, annotations, and environment lighting.**

### Core Pattern

```typescript
// productViewer.ts
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader';

function createProductViewer(container: HTMLElement, modelUrl: string) {
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance',
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.minDistance = 1;
  controls.maxDistance = 10;
  controls.maxPolarAngle = Math.PI / 2;  // prevent going below ground

  // Render on demand — only when controls change
  let needsRender = true;
  controls.addEventListener('change', () => { needsRender = true; });

  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    if (needsRender) {
      renderer.render(scene, camera);
      needsRender = false;
    }
  }
  animate();
}
```

### Key Rules
- Always use render-on-demand for static product viewers (massive GPU savings)
- Load HDR environment map for realistic reflections (`RGBELoader` or `@react-three/drei` `<Environment>`)
- Center model on load: compute bounding box, offset position, fit camera
- Add ground plane or contact shadow for visual grounding

---

## Hero Scene Architecture

**Ambient, auto-playing 3D animation as a page centerpiece. No user interaction. Must not block page load.**

### Core Pattern

```typescript
// heroScene.ts
function initHeroScene(canvas: HTMLCanvasElement) {
  // Lazy initialization — only start when canvas is visible
  const observer = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
      observer.disconnect();
      buildScene(canvas);
    }
  }, { threshold: 0.1 });
  observer.observe(canvas);
}

function buildScene(canvas: HTMLCanvasElement) {
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));  // aggressive clamp for hero

  // Pause rendering when tab is hidden
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) cancelAnimationFrame(rafId);
    else animate();
  });
}
```

### Key Rules
- Lazy-init with IntersectionObserver — never block page load
- Clamp pixel ratio to 1.5 for hero scenes (visual quality vs. performance)
- Pause animation when tab is hidden (save battery)
- Use `alpha: true` to composite over page background
- Keep hero models under 2MB compressed
- Provide a CSS fallback (gradient/image) while loading

---

## Framework Integration Patterns

### React / Next.js (without R3F)

```tsx
// useThreeScene.ts — custom hook pattern
import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function useThreeScene(containerRef: React.RefObject<HTMLDivElement>) {
  const sceneRef = useRef<{ scene: THREE.Scene; renderer: THREE.WebGLRenderer } | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);

    containerRef.current.appendChild(renderer.domElement);
    sceneRef.current = { scene, renderer };

    // ResizeObserver instead of window.resize
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      renderer.dispose();
      containerRef.current?.removeChild(renderer.domElement);
    };
  }, []);

  return sceneRef;
}
```

### React Three Fiber

```tsx
// Scene.tsx — R3F pattern
import { Canvas } from '@react-three/fiber';
import { Environment, OrbitControls, useGLTF } from '@react-three/drei';
import { Suspense } from 'react';

function Model({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  return <primitive object={scene} />;
}

export function ProductScene({ modelUrl }: { modelUrl: string }) {
  return (
    <Canvas
      camera={{ position: [0, 1, 5], fov: 45 }}
      dpr={[1, 2]}
      gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
    >
      <Suspense fallback={null}>
        <Model url={modelUrl} />
        <Environment preset="studio" />
      </Suspense>
      <OrbitControls enableDamping dampingFactor={0.05} />
    </Canvas>
  );
}
```

### Vue 3

```typescript
// useThreeScene.ts — composable pattern
import { onMounted, onUnmounted, ref, Ref } from 'vue';
import * as THREE from 'three';

export function useThreeScene(containerRef: Ref<HTMLElement | null>) {
  const renderer = ref<THREE.WebGLRenderer | null>(null);

  onMounted(() => {
    if (!containerRef.value) return;
    renderer.value = new THREE.WebGLRenderer({ antialias: true });
    containerRef.value.appendChild(renderer.value.domElement);
    // ... scene setup
  });

  onUnmounted(() => {
    renderer.value?.dispose();
  });

  return { renderer };
}
```

### Vanilla JS

```javascript
// threeManager.js — class-based for vanilla
export class ThreeManager {
  constructor(container) {
    this.container = container;
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    container.appendChild(this.renderer.domElement);
    this._setupResize();
  }

  _setupResize() {
    this.ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    });
    this.ro.observe(this.container);
  }

  destroy() {
    this.ro.disconnect();
    this.renderer.dispose();
    this.container.removeChild(this.renderer.domElement);
  }
}
```
