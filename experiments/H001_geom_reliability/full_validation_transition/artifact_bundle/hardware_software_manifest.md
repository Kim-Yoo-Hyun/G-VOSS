# H001 Hardware And Software Manifest

Last updated: 2026-06-13 KST

This manifest records the local verification environment for the current H001
paper-facing full-validation artifacts. It is not a new experiment result and
does not change metric claims.

## Verification Host

Observed on 2026-06-13 KST:

```text
OS: Ubuntu 24.04.4 LTS
kernel: Linux user-Z890-UD 6.17.0-29-generic #29~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Mon May 11 10:30:58 UTC 2 x86_64
system memory: 62 GiB
swap: 8.0 GiB
GPU: NVIDIA GeForce RTX 5090
GPU memory: 32607 MiB
NVIDIA driver: 580.159.03
Docker: Docker version 29.5.2, build 79eb04c
Docker Compose: v5.1.4
Python: 3.12.3
git commit observed: 575592c
```

## Docker Images

```text
h001-geom-reliability:latest
image id: sha256:2e85dd16289063fabb3088c66913113f2ed893691658f31b4da1747e12a4fd87
created: 2026-06-11T14:11:54.71169333+09:00

h001-open3dsg-repro:cu128
image id: sha256:da40c5db6ab9c8ce30506ccf3b59214d35412fb6eb241b83565b33217b3d3d79
created: 2026-05-08T00:16:30.186494437+09:00

h001-aaai-tex:20260611
image id: sha256:461fc997c88979adda2dcf0c2446f4e410d809fd5c8c2a77420527ab4c966dde
created: 2026-06-11T04:09:25.646460649+09:00
```

## Reproducibility Boundary

- The full-validation source metrics and tables are Docker-generated under
  `experiments/H001_geom_reliability/`.
- Large raw datasets, model caches, and feature caches are external or
  regenerated; they are not included in the default 1.4G result bundle.
- The paper-facing result bundle is:

```text
release/h001_full_validation_results_20260611_025158.tar.zst
sha256: d7d8678c5dfc4c2dda54c781220951386cb08cc2d7ca6b5cec908ee9e5e76cea
```
