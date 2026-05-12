# Security Batch Documents

This directory stores grouped analysis and remediation records. Use it for
documents that cover multiple findings or one patch batch.

## Batches

- `F038-F044`: harness mixed-soak findings and patch plan.
- `F045-F046`: post-v184 scan analysis for CPU/memory profile and NCM preflight.
- `F047-F053`: post-v200 scan analysis, patch plan, and H1/H2/H3 reports.
- `F054-F056`: broker observe boundary, Wi-Fi gate fail-closed, and lifecycle
  token namespace fixes.

## Rules

- Analysis documents explain relationship and priority.
- Patch plans define implementation order and validation.
- Patch reports record what actually changed and what passed.
- Finding status is canonical in `../findings/README.md`.
