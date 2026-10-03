// node record.js mr  -> onboarding_mr.mp4 (frames from scene.html seek(t) at 25 fps + audio/<lang>_<i>.mp3)
const { chromium } = require(process.env.PW || "playwright");
const { execFileSync, spawn } = require("child_process");
const path = require("path");
const lang = process.argv[2] || "mr", FPS = 25, dir = __dirname;
const MIN = [9, 7, 7, 7, 6, 10, 8, 5];           // seconds each step needs for its animation
const LEAD = 0.3;                                 // narration starts this long after the step starts
const audio = MIN.map((_, i) => path.join(dir, "audio", `${lang}_${i}.mp3`));
const dur = f => { const o = (() => { try { execFileSync("ffmpeg", ["-i", f], { stdio: "pipe" }); } catch (e) { return e.stderr.toString(); } })();
  const m = o.match(/Duration: (\d+):(\d+):([\d.]+)/); return +m[1] * 3600 + +m[2] * 60 + +m[3]; };
const D = audio.map((f, i) => Math.max(MIN[i], dur(f) + LEAD + 1.3));
(async () => {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
  const p = await b.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2 });
  await p.goto("file://" + path.join(dir, "scene.html"));
  await p.evaluate(() => document.fonts.ready);
  const total = await p.evaluate(([l, d]) => setup(l, d), [lang, D]);
  await p.evaluate(() => document.fonts.ready);
  let t0 = 0; const delays = D.map(d => { const s = t0; t0 += d; return Math.round((s + LEAD) * 1000); });
  const mix = audio.map((_, i) => `[${i + 1}:a]adelay=${delays[i]}[a${i}]`).join(";") + ";" +
    audio.map((_, i) => `[a${i}]`).join("") + `amix=inputs=${audio.length}:normalize=0,apad[a]`;
  const out = path.join(dir, "..", "web", "video", `onboarding_${lang}.mp4`);
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", FPS, "-c:v", "mjpeg", "-i", "-",
    ...audio.flatMap(f => ["-i", f]), "-filter_complex", mix, "-map", "0:v", "-map", "[a]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-pix_fmt", "yuv420p", "-r", FPS,
    "-c:a", "aac", "-b:a", "96k", "-t", total.toFixed(2), "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
  const N = Math.ceil(total * FPS);
  for (let f = 0; f < N; f++) {
    await p.evaluate(t => seek(t), f / FPS);
    const img = await p.screenshot({ type: "jpeg", quality: 90 });
    if (!ff.stdin.write(img)) await new Promise(r => ff.stdin.once("drain", r));
    if (f % 250 === 0) console.log(lang, f, "/", N);
  }
  ff.stdin.end(); await new Promise(r => ff.on("close", r)); await b.close();
  console.log("done", out, total.toFixed(1) + "s", "steps", D.map(d => d.toFixed(1)).join(","));
})();
