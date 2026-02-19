const SPRITE_PATH = "assets/key-visuals/spritesheet-cute-a-qwen.jpg";
const BASE_RECT = { x: 57, y: 41, w: 325, h: 936 };
const BG_KEY_SAMPLE = { x: 0, y: 0 };
const BG_THRESHOLD = 36;
const STAGE_SIZE = 1024;

const STAGE_LAYOUT = {
  base: { x: 352, y: 56, w: 320, h: 922 }
};

const CATEGORY_LAYOUT = {
  top: { widthFactor: 0.63, yFactor: 0.4 },
  bottom: { widthFactor: 0.5, yFactor: 0.58 },
  dress: { widthFactor: 0.71, yFactor: 0.39 },
  shoes: { widthFactor: 0.46, yFactor: 0.9 },
  accessory: { widthFactor: 0.09, yFactor: 0.66 }
};

const CATEGORIES = {
  top: [
    {
      id: "top_pink",
      label: "핑크 리본 티",
      rect: { x: 439, y: 314, w: 174, h: 173 }
    },
    {
      id: "top_mint",
      label: "민트 리본 티",
      rect: { x: 614, y: 314, w: 170, h: 173 }
    },
    {
      id: "top_simple_pink",
      label: "심플 핑크 티",
      rect: { x: 794, y: 318, w: 169, h: 169 }
    }
  ],
  bottom: [
    {
      id: "bottom_shorts_lilac",
      label: "라일락 반바지",
      rect: { x: 468, y: 511, w: 116, h: 126 },
      fit: { widthFactor: 0.42, yFactor: 0.58 }
    },
    {
      id: "bottom_shorts_sparkle",
      label: "글리터 반바지",
      rect: { x: 642, y: 510, w: 115, h: 127 },
      fit: { widthFactor: 0.42, yFactor: 0.58 }
    },
    {
      id: "bottom_skirt_mint",
      label: "민트 스커트",
      rect: { x: 445, y: 677, w: 158, h: 169 },
      fit: { widthFactor: 0.56, yFactor: 0.59 }
    },
    {
      id: "bottom_skirt_mint_2",
      label: "민트 스커트 2",
      rect: { x: 627, y: 687, w: 145, h: 159 },
      fit: { widthFactor: 0.56, yFactor: 0.59 }
    }
  ],
  dress: [
    {
      id: "dress_pink",
      label: "핑크 드레스",
      rect: { x: 773, y: 508, w: 211, h: 348 },
      fit: { widthFactor: 0.71, yFactor: 0.39 }
    }
  ],
  shoes: [
    {
      id: "shoe_sneaker_pink",
      label: "스니커즈 (핑크)",
      rect: { x: 471, y: 873, w: 108, h: 94 },
      fit: { widthFactor: 0.46, yFactor: 0.9 }
    },
    {
      id: "shoe_flat_pink",
      label: "플랫슈즈 (핑크)",
      rect: { x: 644, y: 875, w: 108, h: 92 },
      fit: { widthFactor: 0.45, yFactor: 0.9 }
    },
    {
      id: "shoe_sneaker_mint",
      label: "스니커즈 (민트)",
      rect: { x: 813, y: 874, w: 134, h: 87 },
      fit: { widthFactor: 0.5, yFactor: 0.9 }
    }
  ],
  accessory: [
    {
      id: "acc_bracelet_set",
      label: "비즈 팔찌 세트",
      parts: [
        {
          rect: { x: 622, y: 662, w: 42, h: 57 },
          fit: { widthFactor: 0.09, yFactor: 0.66, xOffset: -108, yOffset: 0 }
        },
        {
          rect: { x: 734, y: 662, w: 42, h: 57 },
          fit: { widthFactor: 0.09, yFactor: 0.66, xOffset: 108, yOffset: 0 }
        }
      ]
    }
  ]
};

const state = {
  top: "",
  bottom: "",
  dress: "",
  shoes: "",
  accessory: ""
};

const dom = {
  topSelect: document.getElementById("topSelect"),
  bottomSelect: document.getElementById("bottomSelect"),
  dressSelect: document.getElementById("dressSelect"),
  shoesSelect: document.getElementById("shoesSelect"),
  accessorySelect: document.getElementById("accessorySelect"),
  randomBtn: document.getElementById("randomBtn"),
  resetBtn: document.getElementById("resetBtn"),
  savePngBtn: document.getElementById("savePngBtn"),
  stage: document.getElementById("stage")
};

const ctx = dom.stage.getContext("2d");
ctx.imageSmoothingEnabled = true;
ctx.imageSmoothingQuality = "high";

const sprite = new Image();
const cropCache = new Map();
let bgColor = { r: 241, g: 241, b: 241 };

function getItemById(category, id) {
  return CATEGORIES[category].find((item) => item.id === id);
}

function drawRoundedBackdrop() {
  ctx.clearRect(0, 0, STAGE_SIZE, STAGE_SIZE);
  const grad = ctx.createLinearGradient(0, 0, 0, STAGE_SIZE);
  grad.addColorStop(0, "#fff8fb");
  grad.addColorStop(1, "#eef5ff");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, STAGE_SIZE, STAGE_SIZE);

  const glow = ctx.createRadialGradient(512, 120, 20, 512, 120, 250);
  glow.addColorStop(0, "#ffffffdd");
  glow.addColorStop(1, "#ffffff00");
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, STAGE_SIZE, STAGE_SIZE);
}

function createCropWithTransparency(rect) {
  const key = `${rect.x}:${rect.y}:${rect.w}:${rect.h}`;
  if (cropCache.has(key)) {
    return cropCache.get(key);
  }

  const off = document.createElement("canvas");
  off.width = rect.w;
  off.height = rect.h;
  const offCtx = off.getContext("2d");
  offCtx.drawImage(
    sprite,
    rect.x,
    rect.y,
    rect.w,
    rect.h,
    0,
    0,
    rect.w,
    rect.h
  );

  const imgData = offCtx.getImageData(0, 0, rect.w, rect.h);
  const data = imgData.data;

  const isBg = (pixelIndex) => {
    const dr = data[pixelIndex] - bgColor.r;
    const dg = data[pixelIndex + 1] - bgColor.g;
    const db = data[pixelIndex + 2] - bgColor.b;
    return (dr * dr) + (dg * dg) + (db * db) <= BG_THRESHOLD * BG_THRESHOLD;
  };

  // JPG artifacts make direct key-color removal unstable.
  // Flood-fill from borders keeps only connected background transparent.
  const visited = new Uint8Array(rect.w * rect.h);
  const queue = new Int32Array(rect.w * rect.h);
  let qHead = 0;
  let qTail = 0;

  const enqueue = (x, y) => {
    const pos = y * rect.w + x;
    if (visited[pos]) return;
    const pixelIndex = pos * 4;
    if (!isBg(pixelIndex)) return;

    visited[pos] = 1;
    queue[qTail] = pos;
    qTail += 1;
  };

  for (let x = 0; x < rect.w; x += 1) {
    enqueue(x, 0);
    enqueue(x, rect.h - 1);
  }
  for (let y = 1; y < rect.h - 1; y += 1) {
    enqueue(0, y);
    enqueue(rect.w - 1, y);
  }

  while (qHead < qTail) {
    const pos = queue[qHead];
    qHead += 1;
    const pixelIndex = pos * 4;
    data[pixelIndex + 3] = 0;

    const x = pos % rect.w;
    const y = Math.floor(pos / rect.w);
    if (x > 0) enqueue(x - 1, y);
    if (x < rect.w - 1) enqueue(x + 1, y);
    if (y > 0) enqueue(x, y - 1);
    if (y < rect.h - 1) enqueue(x, y + 1);
  }

  offCtx.putImageData(imgData, 0, 0);
  cropCache.set(key, off);
  return off;
}

function resolveFit(category, itemFit = {}) {
  const base = CATEGORY_LAYOUT[category];
  return {
    widthFactor: itemFit.widthFactor ?? base.widthFactor,
    yFactor: itemFit.yFactor ?? base.yFactor,
    xOffset: itemFit.xOffset ?? 0,
    yOffset: itemFit.yOffset ?? 0
  };
}

function drawOnePart(category, rect, fitOverrides = {}) {
  const layer = createCropWithTransparency(rect);
  const fit = resolveFit(category, fitOverrides);
  const base = STAGE_LAYOUT.base;

  const targetW = Math.round(base.w * fit.widthFactor);
  const targetH = Math.round((rect.h / rect.w) * targetW);
  const targetX = Math.round(base.x + ((base.w - targetW) / 2) + fit.xOffset);
  const targetY = Math.round(base.y + (base.h * fit.yFactor) + fit.yOffset);
  ctx.drawImage(layer, targetX, targetY, targetW, targetH);
}

function drawItem(category, id) {
  if (!id) return;
  const item = getItemById(category, id);
  if (!item) return;

  if (item.parts?.length) {
    for (const part of item.parts) {
      drawOnePart(category, part.rect, part.fit);
    }
    return;
  }

  drawOnePart(category, item.rect, item.fit);
}

function render() {
  drawRoundedBackdrop();

  const base = createCropWithTransparency(BASE_RECT);
  const avatar = STAGE_LAYOUT.base;
  ctx.drawImage(base, avatar.x, avatar.y, avatar.w, avatar.h);

  if (state.dress) {
    drawItem("dress", state.dress);
  } else {
    drawItem("bottom", state.bottom);
    drawItem("top", state.top);
  }

  drawItem("shoes", state.shoes);
  drawItem("accessory", state.accessory);
}

function buildSelect(category, select) {
  select.innerHTML = "";
  const none = document.createElement("option");
  none.value = "";
  none.textContent = "없음";
  select.appendChild(none);

  for (const item of CATEGORIES[category]) {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.label;
    select.appendChild(option);
  }
}

function syncUiFromState() {
  dom.topSelect.value = state.top;
  dom.bottomSelect.value = state.bottom;
  dom.dressSelect.value = state.dress;
  dom.shoesSelect.value = state.shoes;
  dom.accessorySelect.value = state.accessory;
}

function resetState() {
  state.top = "top_mint";
  state.bottom = "bottom_shorts_lilac";
  state.dress = "";
  state.shoes = "shoe_flat_pink";
  state.accessory = "";
  syncUiFromState();
  render();
}

function randomState() {
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)].id;
  const useDress = Math.random() < 0.35;

  state.dress = useDress ? pick(CATEGORIES.dress) : "";
  state.top = useDress ? "" : pick(CATEGORIES.top);
  state.bottom = useDress ? "" : pick(CATEGORIES.bottom);
  state.shoes = pick(CATEGORIES.shoes);
  state.accessory = Math.random() < 0.45 ? pick(CATEGORIES.accessory) : "";

  syncUiFromState();
  render();
}

function savePng() {
  const a = document.createElement("a");
  a.href = dom.stage.toDataURL("image/png");
  a.download = `dressroom-look-${Date.now()}.png`;
  a.click();
}

function wireEvents() {
  dom.topSelect.addEventListener("change", (e) => {
    state.top = e.target.value;
    if (state.top) {
      state.dress = "";
      dom.dressSelect.value = "";
    }
    render();
  });

  dom.bottomSelect.addEventListener("change", (e) => {
    state.bottom = e.target.value;
    if (state.bottom) {
      state.dress = "";
      dom.dressSelect.value = "";
    }
    render();
  });

  dom.dressSelect.addEventListener("change", (e) => {
    state.dress = e.target.value;
    if (state.dress) {
      state.top = "";
      state.bottom = "";
      dom.topSelect.value = "";
      dom.bottomSelect.value = "";
    }
    render();
  });

  dom.shoesSelect.addEventListener("change", (e) => {
    state.shoes = e.target.value;
    render();
  });

  dom.accessorySelect.addEventListener("change", (e) => {
    state.accessory = e.target.value;
    render();
  });

  dom.randomBtn.addEventListener("click", randomState);
  dom.resetBtn.addEventListener("click", resetState);
  dom.savePngBtn.addEventListener("click", savePng);
}

function initSelects() {
  buildSelect("top", dom.topSelect);
  buildSelect("bottom", dom.bottomSelect);
  buildSelect("dress", dom.dressSelect);
  buildSelect("shoes", dom.shoesSelect);
  buildSelect("accessory", dom.accessorySelect);
}

sprite.onload = () => {
  const sample = document.createElement("canvas");
  sample.width = 1;
  sample.height = 1;
  const sampleCtx = sample.getContext("2d");
  sampleCtx.drawImage(sprite, BG_KEY_SAMPLE.x, BG_KEY_SAMPLE.y, 1, 1, 0, 0, 1, 1);
  const pixel = sampleCtx.getImageData(0, 0, 1, 1).data;
  bgColor = { r: pixel[0], g: pixel[1], b: pixel[2] };

  initSelects();
  wireEvents();
  resetState();
};

sprite.onerror = () => {
  alert("스프라이트 시트를 불러오지 못했습니다.");
};

sprite.src = SPRITE_PATH;
