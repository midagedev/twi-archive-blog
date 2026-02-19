# Copilot Instructions for Dress Game

## Project Overview
**Dress Room** is a browser-based dress-up game targeting pre-teens (10-14 years). The codebase is currently in the specification and asset generation phase, not yet a full implementation. The project has two major streams:
1. **Game Specification & UX Design** (GAME_SPEC.md)
2. **AI Art Generation Pipeline** (PROMPT_PLAYBOOK.md, prompts/, scripts/)

## Architecture & Major Components

### Asset Generation Pipeline (Current Focus)
The project uses **fal.ai** image generation models to create consistent 2D anime-style assets. All assets follow strict constraints:
- **Model Strategy**: Flux/Recraft for key visuals, reference-based generation preferred for parts
- **Prompt Structure**: Fixed 9-block template (STYLE_LOCK → QUALITY_LOCK → ASSET_LOCK → SUBJECT → SCENE → COMPOSITION → COLOR → OUTPUT → NEGATIVE_LOCK)
- **Consistency Engine**: 
  - Model lock: same model per batch
  - Seed policy: fixed master seed (424242) for key visuals, category-specific seeds for parts (hair 10101, top 20202, etc.)
  - QA gates: immediate regeneration if 3D artifacts, blur, or anatomy errors appear

**Key File References**:
- [PROMPT_PLAYBOOK.md](PROMPT_PLAYBOOK.md) - 9 principles + template structure
- [scripts/fal_generate.sh](scripts/fal_generate.sh) - CLI wrapper for fal.ai API (sync/queue modes)
- [prompts/PROMPT_PACK.md](prompts/PROMPT_PACK.md) - Ready-to-use prompt templates

### Game Design (Upcoming Implementation)
Browser-based, HTML/CSS/JS, no backend. **Paper-doll system** with layering logic:
- 7 categories: Hair, Top, Bottom, Dress, Shoes, Accessory, Background
- **Conflict rule**: Dress ↔ Top/Bottom (mutually exclusive)
- **Success metrics**: <3min session, <100ms outfit change latency, <10sec first interaction

**Key File References**:
- [GAME_SPEC.md](GAME_SPEC.md#5-feature-scope) - MVP features, responsive layout (desktop ≥1024px, mobile <1024px)
- [GAME_SPEC.md](GAME_SPEC.md#4-core-game-loop) - Core UX flow

## Critical Workflows & Commands

### Generate Assets (Image Generation)
```bash
export FAL_KEY="your_fal_api_key"
./scripts/fal_generate.sh <model> <prompt_file> <output_file> [image_size] [seed] [mode]

# Examples:
./scripts/fal_generate.sh fal-ai/flux/dev prompts/key-visual-pastel-v2.txt assets/key-visuals/kv-v2.jpg landscape_16_9 424242 sync
./scripts/fal_generate.sh fal-ai/flux/dev prompts/avatar-base-anime-v4-flux.txt assets/avatars/base.png square_hd 10101 queue
```

**Image Size Conventions**:
- Key visuals: `landscape_16_9`
- Avatar/items/accessories: `square_hd`

**Mode Choices**:
- `sync`: blocks until complete, good for single images
- `queue`: async with 2s polling, good for batch jobs

### Quality Gate Checklist
Before accepting generated assets, verify:
1. ✓ Style consistency (pastel tones, 2D cel shading match master)
2. ✓ Clean silhouettes (readable at thumbnail size)
3. ✓ Layer compatibility (no overlapping outlines for parts)
4. ✓ No 3D artifacts (plastic gloss, volumetric light, high relief)
5. ✓ No prohibited elements (text, watermark, distorted anatomy)

Failing any check → regenerate immediately (see [PROMPT_PLAYBOOK.md](PROMPT_PLAYBOOK.md#8-재생성-규칙)).

## Project Conventions & Patterns

### Prompt File Organization
- **v1 prompts**: Initial experiments (avatar-base-anime-v1.txt)
- **v2 prompts**: Recraft model iterations
- **v3 prompts**: Flux model trials
- **v4 prompts**: Latest Flux refinements ("ultra" = final polish)

Files named `-ultra` are production-ready.

### Seed & Determinism Policy
- Fixed seeds ensure reproducible generations
- Use same seed when iterating on same asset type
- Document seed changes in commit messages

### Asset Directory Structure (Planned)
```
assets/
  key-visuals/      # Hero images for UI
  avatars/          # Full-body bases
  clothing/         # Tops, bottoms, dresses, shoes
  accessories/      # Hats, scarves, stickers
  backgrounds/      # Stage/room settings
```

### Responsive Design Pattern
When implementing frontend:
- **Desktop** (≥1024px): 3-column layout (categories | avatar stage | item grid)
- **Mobile** (<1024px): Stack vertically with sticky action bar at bottom
- All buttons must be touch-friendly (min 44px tap target)

## Integration Points & External Dependencies

### fal.ai API
- **Authentication**: FAL_KEY environment variable required
- **Models Used**:
  - `fal-ai/flux/dev` - Default for high-quality assets
  - `fal-ai/recraft/v3/text-to-image` - Alternative for style consistency
  - Reference-based editing preferred over text-only for parts
- **Rate Limiting**: Check fal.ai dashboard; queue mode recommended for batch jobs

### Asset Versioning
Prompts are versioned (v1→v4) to track model/style evolution. Keep git history of both prompts and generated images to track regressions.

## Development Patterns to Avoid

1. **Don't**: Use multiple models in same asset batch (breaks style consistency)
2. **Don't**: Skip QA gates on mediocre generations (saves time but pollutes asset library)
3. **Don't**: Change prompt template order (the 9-block structure is load-bearing for consistency)
4. **Don't**: Hardcode image dimensions (use fal.ai size enums)
5. **Don't**: Commit FAL_KEY or other secrets to git

## Questions to Ask Before Starting Work

- **For asset generation**: Which model/version? What QA criteria? Should we try reference editing?
- **For game code**: Desktop-first or mobile-first implementation? Real canvas rendering or SVG layers?
- **For documentation**: Is this a new prompt variant (document in PROMPT_PACK.md) or iteration on existing?
