---
name: threejs-architect
description: Use when building 3D experiences with Three.js — product configurators, scroll-driven animations, interactive viewers, marketing hero scenes, data visualizations, architecture renderings, 3D UI components. Triggers on requests involving WebGL, Three.js, 3D rendering, GLB/glTF/OBJ/FBX models, scene setup, camera systems, scroll-driven 3D animation, GPU performance optimization, or integrating 3D into React, Next.js, Vue, or vanilla JS projects. Also triggers on terms like configurator, 3D viewer, hero animation, orbit controls, raycasting, or mesh instancing.
---

# Three.js Implementation Architect

## Overview

Production-grade Three.js implementation skill for a professional development company. Designs and builds high-quality 3D experiences across client projects — configurators, scroll animations, viewers, hero scenes, visualizations — with clean architecture, cross-device performance, and modular code that integrates into existing production codebases.

**Core priorities:** Performance, maintainability, modular architecture, cross-device compatibility, production-ready code.

**Critical rule:** Never generate .md files for implementation or architecture. All output must be real code files. Never skip discovery or architecture phases before coding.

## Workflow

```
Phase 0  ·  CODEBASE SCAN        →  Analyze project stack + existing 3D usage
Phase 1  ·  FEASIBILITY           →  Determine if Three.js is the right tool
Phase 2  ·  REQUIREMENTS          →  Interactive questions about the 3D feature
Phase 3  ·  ARCHITECTURE DESIGN   →  Design scene architecture before coding
Phase 4  ·  BUILD CONFIRMATION    →  Get approval before generating code
Phase 5  ·  CODE GENERATION       →  Produce modular, production-ready code
Phase 6  ·  REVIEW + LEARN        →  Capture feedback, update templates
```

---

## Phase 0 — Codebase Scanner

Before doing anything, inspect the project. Use Glob/Grep/Read to detect:

| Signal | Files to check |
|--------|---------------|
| Framework | `package.json`, `next.config.*`, `vite.config.*`, `nuxt.config.*`, `angular.json` |
| Build system | `webpack.config.*`, `vite.config.*`, `tsconfig.json`, `rollup.config.*` |
| Rendering | SSR/SSG/CSR — check Next.js `app/` vs `pages/`, meta framework configs |
| Animation | GSAP, Framer Motion, anime.js, Lottie — check `package.json` dependencies |
| State | Redux, Zustand, Pinia, Jotai, MobX — check imports and stores |
| Routing | Next.js App Router, React Router, Vue Router |
| Mobile | viewport meta tags, responsive CSS, touch event handlers |
| SEO | `next/head`, meta tags, SSR rendering, `robots.txt` |
| Existing 3D | `three`, `@react-three/fiber`, `@react-three/drei`, `babylonjs` in deps |

Output a structured analysis:

```
 ──────────────────────────────────────────────────────────
  Phase 0  ·  PROJECT ANALYSIS
 ──────────────────────────────────────────────────────────
  Framework         :  [detected]
  Build system      :  [detected]
  Rendering         :  [SSR / SSG / CSR]
  Animation libs    :  [detected or none]
  State management  :  [detected or none]
  Mobile needs      :  [yes / no + details]
  SEO constraints   :  [yes / no + details]
  Existing Three.js :  [yes / no + details]
  Integration level :  [easy / moderate / complex]
 ──────────────────────────────────────────────────────────
```

---

## Phase 1 — Feasibility Engine

Determine whether Three.js is the correct solution. Evaluate:

- Scene complexity + polygon count estimates
- GPU cost on desktop and mobile
- Bundle size impact (~150KB min for three.js core)
- SEO impact (canvas elements are not crawlable)
- Whether CSS/Canvas/Lottie/video would achieve the same result

Return one verdict:

| Verdict | When |
|---------|------|
| `THREE_JS_RECOMMENDED` | Complex 3D, interactivity, or real-time rendering needed |
| `THREE_JS_POSSIBLE_WITH_OPTIMIZATION` | Feasible but requires LOD, lazy loading, or mobile fallbacks |
| `BETTER_ALTERNATIVE` | CSS animation, Canvas 2D, Lottie, or video would be simpler and faster |

If `BETTER_ALTERNATIVE`, suggest the specific alternative and why.

---

## Phase 2 — Interactive Requirements

Use AskUserQuestion to gather requirements. Load with `ToolSearch` → `select:AskUserQuestion` first.

**Question 1 — Feature type:**

```js
AskUserQuestion({
  questions: [{
    question: "What type of 3D feature are we building?",
    header: "3D Feature Type",
    multiSelect: false,
    options: [
      { label: "Product configurator", description: "Users customize materials, parts, or options on a 3D model" },
      { label: "Scroll animation", description: "Camera or objects animate as the user scrolls the page" },
      { label: "Interactive 3D viewer", description: "Users orbit, zoom, and inspect a 3D model" },
      { label: "Landing page hero", description: "Animated 3D scene as a visual centerpiece" },
      { label: "Data visualization", description: "3D charts, graphs, or spatial data rendering" },
      { label: "Other", description: "Architecture rendering, simulation, or custom 3D UI" }
    ]
  }]
})
```

**Question 2 — Adaptive follow-ups (ask in one batch, skip confirmed answers):**

```js
AskUserQuestion({
  questions: [
    {
      question: "Will users interact with the 3D model?",
      header: "Interaction",
      multiSelect: false,
      options: [
        { label: "Yes — orbit, click, drag", description: "Users control camera or select objects" },
        { label: "Scroll-driven only", description: "Animation tied to scroll position, no direct interaction" },
        { label: "View only", description: "Passive display, no user interaction" }
      ]
    },
    {
      question: "Do 3D models already exist?",
      header: "Assets",
      multiSelect: false,
      options: [
        { label: "Yes — GLB/glTF", description: "Optimized format, ready to load" },
        { label: "Yes — FBX/OBJ", description: "Need conversion to GLB for web" },
        { label: "No models yet", description: "Geometry will be created in code or models need to be sourced" }
      ]
    },
    {
      question: "What lighting style?",
      header: "Lighting",
      multiSelect: false,
      options: [
        { label: "Realistic / PBR", description: "Environment maps, physically-based materials" },
        { label: "Stylized / artistic", description: "Flat shading, toon, custom materials" },
        { label: "Minimal", description: "Simple ambient + directional, performance-first" }
      ]
    },
    {
      question: "Must this run smoothly on mobile?",
      header: "Mobile",
      multiSelect: false,
      options: [
        { label: "Yes — mobile-first", description: "Must hit 60fps on mid-range phones" },
        { label: "Yes — acceptable", description: "30fps on mobile is fine, 60fps on desktop" },
        { label: "Desktop only", description: "No mobile support needed" }
      ]
    }
  ]
})
```

---

## Phase 3 — Architecture Design

Before generating code, design the scene architecture. Output:

```
 ──────────────────────────────────────────────────────────
  Phase 3  ·  SCENE ARCHITECTURE
 ──────────────────────────────────────────────────────────

  Scene Management  :  [single scene / scene graph / multi-scene]
  Camera System     :  [perspective / orthographic / system details]
  Lighting          :  [setup description]
  Model Pipeline    :  [GLTFLoader + Draco / procedural / hybrid]
  Texture Strategy  :  [compressed / atlas / lazy-loaded]
  Animation         :  [GSAP / Three.js Clock / AnimationMixer]
  Scroll Integration:  [ScrollTrigger / IntersectionObserver / none]
  UI Sync           :  [React state / events / custom bridge]
  Performance Plan  :  [specific optimizations]

  File Structure
  ├── [file 1]  —  [purpose]
  ├── [file 2]  —  [purpose]
  └── [file N]  —  [purpose]
 ──────────────────────────────────────────────────────────
```

For detailed architecture patterns, see [references/architecture-patterns.md](references/architecture-patterns.md).

---

## Phase 4 — Build Confirmation

Use AskUserQuestion before writing any code:

```js
AskUserQuestion({
  questions: [{
    question: "Architecture approved. How should I generate the code?",
    header: "Build Mode",
    multiSelect: false,
    options: [
      { label: "Full production code (Recommended)", description: "Complete implementation with all optimizations" },
      { label: "Modular components", description: "Standalone modules I can integrate myself" },
      { label: "Prototype first", description: "Quick working version, optimize later" },
      { label: "Highly optimized production", description: "Maximum performance — LOD, instancing, compressed textures, adaptive resolution" }
    ]
  }]
})
```

Only begin coding after confirmation.

---

## Phase 5 — Code Generation

Generate real code files only. Never markdown documentation.

**All generated code must include:**
- Clean modular structure with single-responsibility files
- Clear comments explaining non-obvious decisions
- Mobile-safe rendering (pixel ratio clamping, resize observers)
- Optimized asset loading (lazy, progressive, cached)
- Responsive scene sizing (ResizeObserver, not window.resize)
- Minimal GPU overhead (dispose calls, render-on-demand when possible)

**File naming by stack:**

| Stack | Files |
|-------|-------|
| Vanilla JS | `scene.js`, `camera.js`, `renderer.js`, `lighting.js`, `modelLoader.js`, `animationController.js` |
| React / Next.js | `ThreeScene.tsx`, `useThreeScene.ts`, `useThreeRenderer.ts`, `threeManager.ts` |
| React Three Fiber | `Scene.tsx`, `Model.tsx`, `Lights.tsx`, `Controls.tsx`, `effects/` |
| Vue | `ThreeScene.vue`, `useThreeScene.ts`, `threeManager.ts` |

For performance optimization patterns, see [references/performance-patterns.md](references/performance-patterns.md).
For asset pipeline details, see [references/asset-pipeline.md](references/asset-pipeline.md).

---

## Phase 6 — Review + Learn

After implementation, use AskUserQuestion:

```js
AskUserQuestion({
  questions: [{
    question: "How did the implementation work out?",
    header: "Review",
    multiSelect: false,
    options: [
      { label: "Worked perfectly", description: "No issues — template this pattern" },
      { label: "Needed small fixes", description: "Minor adjustments — I'll describe them" },
      { label: "Major issues", description: "Architecture or performance problems — needs rework" }
    ]
  }]
})
```

If fixes are reported, analyze: incorrect assumptions, architecture flaws, performance issues, asset pipeline issues. Update internal patterns for future use.

### Self-Learning Storage

After each implementation, append to `~/.claude/skills/threejs-architect/logs/implementations.jsonl`:

```json
{
  "timestamp": "ISO-8601",
  "project_id": "sha256_of_path[:8]",
  "feature_type": "configurator | scroll | viewer | hero | viz | other",
  "stack": { "framework": "", "build": "", "state": "" },
  "scene_type": "",
  "models_format": "glb | fbx | procedural",
  "lighting": "pbr | stylized | minimal",
  "mobile": true,
  "build_mode": "full | modular | prototype | optimized",
  "review": "perfect | small-fixes | major-issues",
  "fixes_applied": [],
  "files_generated": [],
  "performance_techniques": [],
  "template_candidate": ""
}
```

When a `feature_type + stack` combination has 3+ successful implementations, enable **one-shot mode**: skip Phase 2 questions, present architecture directly, ask only for build confirmation.

---

## Scene Type Detection

Automatically detect scene type from description and route to the right architecture:

| Keywords | Scene Type | Architecture |
|----------|-----------|-------------|
| configurator, customize, options, materials, swap | Configurator | State-driven mesh/material swapping, option panels |
| scroll, parallax, timeline, section | Scroll Animation | GSAP ScrollTrigger, camera path, timeline sync |
| viewer, orbit, inspect, 360 | Product Viewer | OrbitControls, environment map, model hotspots |
| hero, landing, background | Hero Scene | Autoplay animation, lazy init, intersection-based |
| chart, data, graph, spatial | Data Visualization | Instanced meshes, dynamic geometry, color scales |
| building, architecture, floor plan | Architecture Viz | Multi-model loading, section planes, measurement |

For reusable scene templates, see [references/scene-templates.md](references/scene-templates.md).

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `window.devicePixelRatio` unclamped | Clamp to `Math.min(window.devicePixelRatio, 2)` |
| Continuous render loop for static scenes | Use render-on-demand: only re-render on interaction/animation |
| No disposal on unmount | Always call `renderer.dispose()`, `geometry.dispose()`, `material.dispose()`, `texture.dispose()` |
| `window.addEventListener('resize')` | Use `ResizeObserver` on the canvas container instead |
| Loading full-res textures on mobile | Use KTX2/Basis compressed textures, serve smaller variants |
| Forgetting `sRGBEncoding` on textures | Set `texture.colorSpace = THREE.SRGBColorSpace` for color textures |
| Shadow maps on mobile | Disable or use very small shadow maps (512px) on mobile GPUs |
| Blocking main thread with model loading | Use `GLTFLoader` with Draco in a Web Worker via `useLoader` or async patterns |
| No loading state | Always show a loading indicator while assets download |
| Canvas blocks scrolling on mobile | Set `touch-action: none` on canvas, handle pointer events properly |
| `dynamic` with `ssr: false` in Server Component | Add `'use client'` to the wrapper component — App Router requires this |

---

## Quick Reference — Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `three` | Core 3D engine | `npm i three` |
| `@react-three/fiber` | React renderer for Three.js | `npm i @react-three/fiber` |
| `@react-three/drei` | Helpers (OrbitControls, Environment, etc.) | `npm i @react-three/drei` |
| `@react-three/postprocessing` | Post-processing effects | `npm i @react-three/postprocessing` |
| `gsap` | Animation + ScrollTrigger | `npm i gsap` |
| `leva` | Debug GUI for dev | `npm i leva` |
| `three-stdlib` | Extended Three.js utilities | `npm i three-stdlib` |
| `draco3dgltf` | Draco mesh compression decoder | Served from CDN or bundled |
