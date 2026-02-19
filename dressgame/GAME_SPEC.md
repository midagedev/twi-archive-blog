# Dress Room - Browser Game Spec & TODO

## 1) Project Summary
- Project name: Dress Room
- Goal: 12-year-old user can style an avatar quickly and have fun saving looks.
- Platform: Browser (desktop + mobile), no install.
- Scope: HTML/CSS/JavaScript only, local assets, no backend.

## 2) Product Goals
- The player can complete one styling session in under 3 minutes.
- Controls are obvious without tutorial.
- Player can save and reload outfits and export a PNG image.

### Success Metrics (MVP)
- First interaction under 10 seconds after page load.
- Outfit change latency under 100ms on average laptop/mobile browser.
- All core buttons work without reload: `Random`, `Reset`, `Save Outfit`, `Export PNG`.

## 3) Target User & Experience
- Primary user: pre-teen (around 10-14), touch-friendly interaction preferred.
- Session length: 3-10 minutes.
- Motivation:
- Fast creative expression.
- Cute visual feedback.
- Easy sharing via image export.

## 4) Core Game Loop
1. Choose category (hair/top/bottom/dress/shoes/accessory/background).
2. Tap an item thumbnail.
3. Avatar updates instantly.
4. Repeat and compare combinations.
5. Save outfit or export image.

## 5) Feature Scope

### 5.1 MVP Features (Must Have)
- Category tabs with item grid.
- Avatar layered rendering.
- Slot replacement logic.
- Dress conflict rule:
- If dress equipped -> top and bottom are removed.
- If top or bottom equipped while dress active -> dress removed.
- Random outfit generation.
- Reset to default avatar.
- Save up to 10 outfits in localStorage.
- Load saved outfits.
- Export avatar area as PNG.
- Responsive layout (desktop and mobile).

### 5.2 V1.1 Features (Nice to Have)
- Skin tone selector.
- Eye and mouth variation.
- Sticker props (star, heart, sparkles).
- Theme packs (school day, party, winter).
- Light mission system:
- "Create a pink outfit"
- "Use at least one accessory"

## 6) Screen & Layout Design

### 6.1 Desktop Layout (>= 1024px)
- Top bar (fixed): logo + action buttons.
- Left panel: category tabs.
- Center stage: avatar + background.
- Right panel: item grid with scroll.

### 6.2 Mobile Layout (< 1024px)
- Top bar condensed to icon buttons.
- Center stage first (largest area).
- Horizontal category tab strip.
- Item grid below with larger touch targets.
- Sticky bottom action row for major buttons.

### 6.3 Wireframe (Concept)
```txt
+--------------------------------------------------------------+
| Logo | Random | Reset | Save Outfit | Export PNG            |
+-------------------+------------------------+-----------------+
| Categories        | Avatar Stage           | Item Grid       |
| - Hair            | [Background Layer]     | [thumb][thumb]  |
| - Top             | [Avatar Layers]        | [thumb][thumb]  |
| - Bottom          |                        | [scroll...]      |
| - Dress           |                        |                 |
| - Shoes           |                        |                 |
| - Accessory       |                        |                 |
| - Background      |                        |                 |
+-------------------+------------------------+-----------------+
```

## 7) Visual Direction
- Mood: cheerful, soft pastel, sticker-like cute style.
- Avoid visual clutter: keep UI clean with clear iconography.
- Character proportion: anime slim chibi around 3.5-4-head-tall ratio.
- Animation:
- Item select pulse (120ms).
- Avatar fade/scale transition (100-150ms).
- Button hover/tap feedback.

### Typography & Color
- Use playful but readable font (for example: Nunito or Baloo 2).
- Color tokens:
- `--bg-main`: warm light cream
- `--panel`: soft mint
- `--accent`: coral
- `--accent-2`: sky blue
- `--text`: dark slate

## 8) Avatar Layering Spec

### 8.1 Render Order (back -> front)
1. Background
2. Body/Base
3. Hair Back
4. Top or Dress
5. Bottom (if no Dress)
6. Shoes
7. Hair Front/Bangs
8. Accessory
9. FX (optional sparkles)

### 8.2 Canvas and Asset Rules
- Base canvas recommendation: `1024 x 1536`.
- Every wearable asset uses transparent PNG.
- Same anchor point for all wearables to prevent position drift.
- Thumbnail size: `128 x 128`.
- Base avatar rule: base image must use plain bodysuit only (no built-in fashion outfit).
- Body lock rule: each clothing pack targets one body type id (for example `body_a`) and cannot mix with other body ids.

## 9) Content Spec

### 9.1 Initial Item Count Target
- Hair: 12
- Top: 10
- Bottom: 10
- Dress: 8
- Shoes: 8
- Accessory: 12
- Background: 8

### 9.2 Naming Convention
- `category_item_variant.png`
- Examples:
- `hair_bob_brown.png`
- `top_hoodie_mint.png`
- `accessory_starclip_gold.png`
- Body-locked examples:
- `body_a_base.png`
- `top_hoodie_mint_body_a.png`
- `dress_flower_pink_body_a.png`

## 10) Data Model (Draft)
```json
{
  "categories": ["hair", "top", "bottom", "dress", "shoes", "accessory", "background"],
  "items": [
    {
      "id": "top_hoodie_mint",
      "category": "top",
      "layer": 4,
      "thumb": "assets/thumbs/top_hoodie_mint.png",
      "image": "assets/items/top_hoodie_mint.png",
      "tags": ["casual", "mint"]
    }
  ],
  "defaults": {
    "hair": "hair_long_brown",
    "top": "top_tshirt_white",
    "bottom": "bottom_jeans_blue",
    "dress": null,
    "shoes": "shoes_sneaker_white",
    "accessory": null,
    "background": "bg_room_pastel"
  }
}
```

## 11) Technical Plan

### 11.1 File Structure
```txt
/index.html
/style.css
/app.js
/data/items.json
/assets/base/*
/assets/items/*
/assets/thumbs/*
/assets/backgrounds/*
```

### 11.2 JS Module Responsibilities
- State manager: selected items, saved outfits, active category.
- Renderer: apply layered images to stage.
- UI controller: tab switch, item click, button actions.
- Persistence: localStorage read/write with schema version.
- Export: capture stage and save PNG (using canvas/html2canvas).

### 11.3 Storage Schema
- `dressroom:lastState`
- `dressroom:savedOutfits`
- `dressroom:schemaVersion`

## 12) Asset Production Workflow

### 12.1 Option A (Fast Start)
- Build MVP with simple local SVG/PNG placeholders.
- Replace with polished assets incrementally.

### 12.2 Option B (fal.ai Assisted)
- Generate style-consistent packs per category.
- Review and retouch manually for anchor consistency.
- Export transparent PNG and thumbnails.

### 12.3 Security Note
- Never ship API key in frontend code.
- Use local/private script for generation and keep key in environment variable.
- Because a key was exposed in chat, key rotation is recommended before production use.

## 13) QA / Test Checklist
- Category switching updates item grid correctly.
- Slot replacement works for all categories.
- Dress conflict rules always enforced.
- Random button never creates invalid state.
- Save/load works after browser refresh.
- Exported PNG matches current avatar view.
- Mobile touch targets are usable and no overlap occurs.
- No missing image broken links in default set.

## 14) Implementation TODO (Concrete Tasks)

### Phase 1 - Foundation
- [ ] Create `index.html` layout skeleton.
- [ ] Create responsive `style.css` with desktop/mobile breakpoints.
- [ ] Create `app.js` state model and event wiring.
- [ ] Create `data/items.json` schema and sample entries.

### Phase 2 - Core Gameplay
- [ ] Implement category tab switching.
- [ ] Implement item selection and slot replacement.
- [ ] Implement render stack by layer order.
- [ ] Implement dress/top/bottom conflict rules.
- [ ] Implement `Random` and `Reset`.

### Phase 3 - Persistence & Export
- [ ] Implement localStorage save/load of current look.
- [ ] Implement save slots (max 10 outfits).
- [ ] Implement outfit load/delete UI.
- [ ] Implement PNG export of avatar stage.

### Phase 4 - Content & Polish
- [ ] Add complete starter asset pack (at least 40 items total).
- [ ] Add hover/tap animations and selected-state highlight.
- [ ] Improve empty/disabled states for better UX.
- [ ] Add lightweight sound toggle (optional).

### Phase 5 - QA & Release
- [ ] Cross-browser check (Chrome/Safari/Edge).
- [ ] Mobile QA (iOS Safari + Android Chrome).
- [ ] Fix visual alignment issues by category.
- [ ] Final pass on performance and image optimization.

## 15) Decision Log (To Confirm Before Build)
- Confirm art style:
- A) soft pastel cute
- B) bright pop toy-like
- Confirm avatar body type count for MVP:
- A) one base body
- B) two base body options
- Confirm if we include mini-mission feature in first release.

## 16) Game Design Deepening

### 16.1 Play Modes
- Free Mode:
- No objective, player styles freely and saves/exports.
- Challenge Mode:
- One style mission card appears.
- Example cards:
- "Make a spring picnic look"
- "Use 2 blue items"
- "No accessory challenge"

### 16.2 Challenge Scoring (Simple Rules)
- Theme match: up to 60 points.
- Color match: up to 25 points.
- Accessory bonus: up to 15 points.
- Total score: 100 points.
- Reward tiers:
- 80+ -> 3 stars
- 60-79 -> 2 stars
- below 60 -> 1 star

### 16.3 Reward Loop
- Stars unlock cosmetic-only content (new backgrounds/stickers).
- No paywall or competitive pressure.
- Keep loop short:
- Mission select -> style -> score -> reward -> retry.

### 16.4 Child-Friendly UX Rules
- No text-heavy onboarding; use icon plus one-line hints.
- No punishment for low score; always reward at least 1 star.
- Reset confirmation only when current look is unsaved.
- Colorblind-safe contrast for key UI buttons.

## 17) Content Expansion Plan
- Pack 1: School Day
- Pack 2: Weekend Picnic
- Pack 3: Winter Holiday
- Pack 4: Fantasy Princess
- Each pack target:
- 1 background
- 2 hair
- 3 tops
- 3 bottoms or 2 dresses
- 2 shoes
- 3 accessories
