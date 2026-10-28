# DexLab Web

Browser-native experiment catalogue and the first live MuJoCo solver comparison.

## Run

```bash
cd web
npm install
npm run dev
```

Open the printed local URL. WebGPU is used when available; the first frame falls
back to WebGL when the browser does not expose `navigator.gpu`.

## Current scope

The catalogue lists every published DexLab experiment. The incline case runs
locally with MuJoCo 3.17 WebAssembly in three independent solver configurations:
PGS/pyramidal, CG/elliptic, and Newton/elliptic. The remaining experiments link
to their existing reports and recorded evidence until their native assets or
backends are available in the browser.

Live browser results are not interchangeable with the repository's frozen
native evidence. The page reports browser, GPU, MuJoCo version, solver settings,
simulation speed, and counters so the runtime remains auditable.
