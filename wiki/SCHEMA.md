# Wiki Schema

## Domain
AI/ML research, multi-agent systems, open-source AI tooling, paper reviews,
projects (Mythrill · C-Chasm · [[grand-engine-vision]]), studio governance (architecture/)

## Top-level Categories
- `entities/` — concrete entities (projects, systems, characters, infra)
- `concepts/` — abstract concepts (methods, laws, patterns)
- `architecture/` — multi-agent studio governance (roles, cost tiers, validation, model conventions)
- `comparisons/` — comparative analysis
- `queries/` — queries · memos
- `raw/` — source originals (Obsidian vault etc., pre-processing)

## Conventions
- Filenames: lowercase + hyphens preferred (e.g., `transformer-architecture.md`)
  - Exception: when semantic preservation matters (C-Chasm Korean IP docs · characters · systems), `한국어_underscore.md` is allowed
- All pages require YAML frontmatter
- Connect pages via `[[wikilinks]]` (min 2 per page)
- On edit, bump `updated` date
- New pages must be added to `index.md`
- All work logged in `log.md`

## Frontmatter
```yaml
---
title: Page title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary | architecture | project | system | character
tags: [pick from taxonomy below]
sources: [raw/articles/source.md]
confidence: high | medium | low
---
```

### type usage guide
- `entity` — generic entity (infra, pipeline, validation artifact, etc.)
- `project` — work/project unit inside entities/ (e.g., 본편_RPG, C-Chasm_Alpha)
- `system` — game system/mechanic unit inside entities/ (e.g., 연금술_7단계_시스템, DEUS_EX_MACHINA)
- `character` — character inside entities/ (e.g., 아담, THALIS)
- `concept` — abstract concept/law/pattern inside concepts/
- `architecture` — governance doc inside architecture/ (roles, cost tiers, etc.)
- `comparison` / `query` / `summary` — only for their respective folders

## Tag Taxonomy
- **AI/ML**: model, architecture, benchmark, training, inference, fine-tuning
- **Multi-Agent**: agent, orchestration, delegation, multi-agent
- **Tools**: open-source, framework, VS Code, IDE, CLI
- **Research**: paper, survey, review, arxiv
- **People/Orgs**: person, company, lab, project
- **Meta**: comparison, timeline, idea, todo
- **Studio Governance** (architecture/): cost, hardware, prompt, validation, qa, automation, governance, session, log
- **C-Chasm IP**: c-chasm, ip-core, cosmology, lore, directory
- **Mythrill**: mythrill, vfx, mpm, pipeline, llm, verification, spike

## Page Thresholds
- Create a page when a topic appears in 2+ sources or is the central topic of one source
- Split into sub-pages when over 200 lines

## Update Policy
- On conflicting info, record both and mark `contested: true`
- Newer info wins, but preserve prior info
- When multiple SoTs exist for one topic, designate one canonical + place canonical banner on the rest
