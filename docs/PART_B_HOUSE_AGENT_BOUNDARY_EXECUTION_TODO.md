# Part B House Agent Boundary Execution TODO

Last updated: 2026-03-20  
Status: Active implementation checklist derived from `PART_B_HOUSE_AGENT_BOUNDARY_FINAL.md`

## Mission

Make the product-vs-benchmark boundary visible, enforced, and hard to accidentally violate.

## Package

- [x] Add canonical synthesis doc.
- [x] Update Bible and technical appendix with the settled house-agent rule.
- [x] Update roadmap/todo references so new agents see the boundary immediately.
- [x] Add contract assertion tests:
  - [x] public observation contract only
  - [x] public action grammar only
  - [x] scoring independent of house-agent flag
  - [x] leaderboard entries always expose run class / agent type / compliance state
- [x] Add auditable house-agent decision-context field for previews and executed plans.
- [x] Add visible ecology labels:
  - [x] run class
  - [x] agent type
  - [x] contract compliance / benchmark eligibility
- [x] Add concise ecology explainer for:
  - [x] public action grammar
  - [x] same scoring rule
  - [x] house-agent product richness without benchmark privilege
- [x] Verify with tests and smoke checks.

## Done When

- the house-agent boundary is canonical in docs
- the chokepoints are tested in code
- the ecology UI exposes the trust labels directly
- there is no ambiguity about what the house agent may and may not do
