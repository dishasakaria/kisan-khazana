// node record.js            -> sell_smart_pitch.mp4 (scene.html seek(t) frames at 25 fps + Sarvam clips + synth pad)
// node record.js 3,12.5,40  -> frames/qa_<t>.jpg only (quick visual QA, no encode)
const { chromium } = require(process.env.PW || "/opt/node-tools/node_modules/playwright");
const { execFileSync, spawn } = require("child_process");
const path = require("path"), fs = require("fs");
const FPS = 25, dir = __dirname, LEAD = 0.5;
const lines = JSON.parse(fs.readFileSync(path.join(dir, "lines.json")));
const VOICES = { narr: "kavya", ramu: "gokul", shamu: "kabir" };   // keep in sync with tts.py
const MIN = [7, 8, 6.5, 11, 14, 9, 12, 10];                         // seconds each scene needs for its animation
const pcm = f => { const b = execFileSync("ffmpeg", ["-v", "error", "-i", f, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], { maxBuffer: 1 << 26 });
  return new Int16Array(b.buffer, b.byteOffset, b.length >> 1); };
const clips = lines.map(l => {
  const file = path.join(dir, "audio", `${l.id}_${VOICES[l.who]}.mp3`), x = pcm(file), env = [];
  for (let i = 0; i < x.length; i += 320) { let s = 0; const e = Math.min(x.length, i + 320); for (let j = i; j < e; j++) s += x[j] * x[j]; env.push(Math.sqrt(s / (e - i))); }
  const p95 = [...env].sort((a, b) => a - b)[Math.floor(env.length * 0.95)] || 1;
  return { id: l.id, who: l.who, subs: l.subs, file, dur: x.length / 8000, env: env.map(v => +Math.min(1, v / p95).toFixed(2)) };
});
// scene i plays clip i; scene 8 plays s8a then s8b over the end card
const D = [], start = []; let t0 = 0;
for (let i = 0; i < 8; i++) {
  if (i < 7) { clips[i].start = t0 + LEAD; D.push(Math.max(MIN[i], LEAD + clips[i].dur + 0.9)); }
  else { clips[7].start = t0 + 0.6; clips[8].start = clips[7].start + clips[7].dur + 3.0; D.push(Math.max(MIN[7], clips[8].start - t0 + clips[8].dur + 2.2)); }
  start.push(t0); t0 += D[i];
}
const total = t0;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto("file://" + path.join(dir, "scene.html"));
  await p.evaluate(([D, c]) => setup(D, c), [D, clips.map(({ file, ...c }) => c)]);
  await p.evaluate(() => document.fonts.ready);
  const qa = process.argv[2];
  if (qa) {
    fs.mkdirSync(path.join(dir, "frames"), { recursive: true });
    for (const t of qa.split(",").map(Number)) { await p.evaluate(t => seek(t), t);
      await p.screenshot({ path: path.join(dir, "frames", `qa_${t}.jpg`), type: "jpeg", quality: 85 }); }
    console.log("scene starts", start.map(s => s.toFixed(1)).join(","), "total", total.toFixed(1)); return b.close();
  }
  execFileSync("python3", [path.join(dir, "music.py"), total.toFixed(2), path.join(dir, "audio", "music.wav")]);
  const mix = clips.map((c, i) => `[${i + 1}:a]aresample=44100,adelay=${Math.round(c.start * 1000)}:all=1[a${i}]`).join(";") +
    `;[${clips.length + 1}:a]volume=0.5[m];` + clips.map((_, i) => `[a${i}]`).join("") + `[m]amix=inputs=${clips.length + 1}:normalize=0,apad[a]`;
  const out = process.env.OUT || path.join(dir, "sell_smart_pitch.mp4");   // OUT=... renders outside the repo (another agent's git autostash clobbered an in-progress file once)
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", FPS, "-c:v", "mjpeg", "-i", "-",
    ...clips.flatMap(c => ["-i", c.file]), "-i", path.join(dir, "audio", "music.wav"), "-filter_complex", mix, "-map", "0:v", "-map", "[a]",
    "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p", "-r", FPS,
    "-c:a", "aac", "-b:a", "128k", "-t", total.toFixed(2), "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
  const N = Math.ceil(total * FPS);
  for (let f = 0; f < N; f++) {
    await p.evaluate(t => seek(t), f / FPS);
    const img = await p.screenshot({ type: "jpeg", quality: 92 });
    if (!ff.stdin.write(img)) await new Promise(r => ff.stdin.once("drain", r));
    if (f % 250 === 0) console.log(f, "/", N);
  }
  ff.stdin.end(); await new Promise(r => ff.on("close", r)); await b.close();
  console.log("done", out, total.toFixed(1) + "s", "scenes", D.map(d => d.toFixed(1)).join(","));
})();
