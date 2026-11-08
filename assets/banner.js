// claude-cockpit banner — p5.js generative art (Catppuccin Mocha palette)
// Open assets/banner.html in a browser to view; it renders a single static frame.
const W = 1600, H = 640;
const C = {
  base: '#1e1e2e', mantle: '#181825', surface: '#313244', overlay: '#6c7086',
  text: '#cdd6f4', mauve: '#cba6f7', blue: '#89b4fa', sapphire: '#74c7ec',
  teal: '#94e2d5', green: '#a6e3a1', peach: '#fab387', pink: '#f5c2e7', red: '#f38ba8',
};

function setup() {
  createCanvas(W, H);
  pixelDensity(2);
  noLoop();
  randomSeed(7);
  noiseSeed(11);
}

function draw() {
  background(C.base);
  flowField();
  glow(W / 2, H / 2, 520, C.mauve, 38);
  glow(W * 0.2, H * 0.75, 380, C.blue, 26);
  glow(W * 0.82, H * 0.3, 380, C.pink, 22);
  grid();
  panels();
  gauge(W * 0.17, H * 0.5, 120, 0.72, C.teal, 'USAGE');
  gauge(W * 0.83, H * 0.5, 120, 0.46, C.peach, 'BURN');
  centerRings(W / 2, H / 2);
  title();
  scanlines();
  vignette();
}

function glow(x, y, r, col, a) {
  noStroke();
  const c = color(col);
  for (let i = 28; i > 0; i--) {
    c.setAlpha((a / 28) * (1 - i / 28) * 2.2);
    fill(c);
    circle(x, y, (r * i) / 14);
  }
}

function flowField() {
  strokeWeight(1.2);
  noFill();
  const cols = [C.mauve, C.blue, C.sapphire, C.teal, C.pink];
  for (let n = 0; n < 1100; n++) {
    let x = random(-40, W + 40), y = random(-40, H + 40);
    const c = color(random(cols));
    c.setAlpha(random(22, 70));
    stroke(c);
    beginShape();
    for (let s = 0; s < 70; s++) {
      vertex(x, y);
      const a = noise(x * 0.0016, y * 0.0016) * TWO_PI * 2.2;
      x += cos(a) * 5;
      y += sin(a) * 5;
    }
    endShape();
  }
}

function grid() {
  stroke(255, 255, 255, 9);
  strokeWeight(1);
  for (let x = 0; x <= W; x += 40) line(x, 0, x, H);
  for (let y = 0; y <= H; y += 40) line(0, y, W, y);
}

// the three-pane cockpit layout: [ side | claude | side ]
function panels() {
  const m = 36, g = 18, top = 36, bot = H - 36;
  const wSide = 400, wMid = W - 2 * m - 2 * wSide - 2 * g;
  const xs = [m, m + wSide + g, m + wSide + g + wMid + g];
  const ws = [wSide, wMid, wSide];
  const cols = [C.teal, C.mauve, C.peach];
  for (let i = 0; i < 3; i++) {
    fill(24, 24, 37, 120);
    stroke(cols[i] + '88');
    strokeWeight(1.5);
    rect(xs[i], top, ws[i], bot - top, 14);
    // corner brackets
    stroke(cols[i]);
    strokeWeight(3);
    const L = 22, x0 = xs[i], y0 = top, x1 = xs[i] + ws[i], y1 = bot;
    line(x0, y0 + L, x0, y0); line(x0, y0, x0 + L, y0);
    line(x1 - L, y0, x1, y0); line(x1, y0, x1, y0 + L);
    line(x0, y1 - L, x0, y1); line(x0, y1, x0 + L, y1);
    line(x1 - L, y1, x1, y1); line(x1, y1, x1, y1 - L);
    // fake status ticks
    noStroke();
    for (let k = 0; k < (i === 1 ? 0 : 6); k++) {
      const bw = random(40, ws[i] - 90);
      fill(cols[i] + '33');
      rect(xs[i] + 24, bot - 34 - k * 14, bw, 5, 3);
    }
  }
}

function gauge(cx, cy, r, v, col, label) {
  push();
  translate(cx, cy);
  noFill();
  strokeCap(ROUND);
  stroke(255, 255, 255, 22);
  strokeWeight(14);
  arc(0, 0, r * 2, r * 2, PI * 0.75, PI * 2.25);
  stroke(col);
  strokeWeight(14);
  arc(0, 0, r * 2, r * 2, PI * 0.75, PI * 0.75 + PI * 1.5 * v);
  // tick marks
  strokeWeight(2);
  for (let i = 0; i <= 30; i++) {
    const a = PI * 0.75 + (PI * 1.5 * i) / 30;
    stroke(i / 30 <= v ? col : '#6c708688');
    const r1 = r + 18, r2 = r + (i % 5 === 0 ? 32 : 26);
    line(cos(a) * r1, sin(a) * r1, cos(a) * r2, sin(a) * r2);
  }
  noStroke();
  fill(C.text);
  textAlign(CENTER, CENTER);
  textFont('Menlo');
  textStyle(BOLD);
  textSize(38);
  text(round(v * 100) + '%', 0, -4);
  textStyle(NORMAL);
  textSize(13);
  fill(col);
  text(label, 0, 32);
  pop();
}

function centerRings(cx, cy) {
  noFill();
  for (let i = 0; i < 7; i++) {
    const r = 70 + i * 26;
    const c = color(i % 2 ? C.mauve : C.blue);
    c.setAlpha(150 - i * 14);
    stroke(c);
    strokeWeight(i === 0 ? 3 : 1.5);
    const gap = 0.35 + i * 0.12, start = i * 0.9;
    arc(cx, cy, r * 2, r * 2, start, start + TWO_PI - gap);
  }
  // orbiting nodes
  noStroke();
  for (let i = 0; i < 18; i++) {
    const a = (i / 18) * TWO_PI + 0.3, r = 70 + (i % 7) * 26;
    const c = color(random([C.teal, C.pink, C.peach, C.green]));
    glow(cx + cos(a) * r, cy + sin(a) * r, 26, c, 70);
    fill(c);
    circle(cx + cos(a) * r, cy + sin(a) * r, 7);
  }
  fill(C.mantle);
  stroke(C.mauve);
  strokeWeight(3);
  circle(cx, cy, 120);
  // prompt glyph  >_
  noStroke();
  fill(C.mauve);
  textAlign(CENTER, CENTER);
  textFont('Menlo');
  textStyle(BOLD);
  textSize(44);
  text('>_', cx, cy - 2);
}

function title() {
  textAlign(CENTER, CENTER);
  textFont('Menlo');
  textStyle(BOLD);
  textSize(56);
  noStroke();
  fill(C.mauve + '55');
  text('claude-cockpit', W / 2 + 3, H - 98 + 3);
  fill(C.text);
  text('claude-cockpit', W / 2, H - 98);
  textStyle(NORMAL);
  textSize(16);
  fill(C.overlay);
  text('usage · token burn · system · git', W / 2, H - 58);
}

function scanlines() {
  stroke(0, 0, 0, 22);
  strokeWeight(1);
  for (let y = 0; y < H; y += 3) line(0, y, W, y);
}

function vignette() {
  noFill();
  for (let i = 0; i < 60; i++) {
    stroke(17, 17, 27, (i / 60) * 5);
    strokeWeight(14);
    rect(-i, -i, W + 2 * i, H + 2 * i);
  }
  const ctx = drawingContext;
  const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, W * 0.62);
  g.addColorStop(0, 'rgba(17,17,27,0)');
  g.addColorStop(1, 'rgba(17,17,27,0.65)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}
