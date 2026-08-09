/**
 * Renders assets/signal-{dark,light}{,-sm}.svg from the contribution calendar.
 *
 * Replaces github-readme-stats, whose hosts went down (503 DEPLOYMENT_PAUSED on
 * the official one, Vercel SSO on the community mirror) and left this profile
 * showing broken images. Owning the render means no third-party host can break
 * the page again, and the panel matches the rest of the profile's design system.
 *
 * The numbers reflect what a logged-out visitor can see. Private-repo work is
 * included because "Include private contributions on my profile" is enabled in
 * account settings; turning it off would silently shrink every figure here.
 *
 * Usage: GITHUB_TOKEN=... USER=Douglas-Strey node .github/scripts/signal.mjs
 */
import { writeFileSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..");
const USER = process.env.USER_LOGIN || "Douglas-Strey";
const TOKEN = process.env.GITHUB_TOKEN;
if (!TOKEN) throw new Error("GITHUB_TOKEN is required");

const FONTS = Object.fromEntries(
  [["regular", 400], ["medium", 500], ["semibold", 600]].map(([f, w]) => [
    w,
    readFileSync(join(HERE, "fonts", `${f}.b64`), "utf8").trim(),
  ]),
);
const FONT_CSS = Object.entries(FONTS)
  .map(([w, b64]) =>
    `@font-face{font-family:GM;font-style:normal;font-weight:${w};` +
    `src:url(data:font/woff2;base64,${b64}) format('woff2')}`)
  .join("");

const DARK = { bg: "#0D1117", line: "#212C38", text: "#D8E0E9", dim: "#93A3B2", mint: "#3DDC97" };
const LIGHT = { bg: "#FFFFFF", line: "#DEE6EE", text: "#131E29", dim: "#4B5D6B", mint: "#0A7E57" };

// ---------------------------------------------------------------- data
const QUERY = `query($login:String!){
  user(login:$login){ contributionsCollection{ contributionCalendar{
    totalContributions
    weeks{ contributionDays{ date contributionCount } }
  } } }
}`;

async function fetchCalendar() {
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: { authorization: `bearer ${TOKEN}`, "content-type": "application/json" },
    body: JSON.stringify({ query: QUERY, variables: { login: USER } }),
  });
  if (!res.ok) throw new Error(`GraphQL HTTP ${res.status}: ${await res.text()}`);
  const json = await res.json();
  if (json.errors) throw new Error(`GraphQL: ${JSON.stringify(json.errors)}`);
  return json.data.user.contributionsCollection.contributionCalendar;
}

function measure(calendar) {
  const days = calendar.weeks
    .flatMap((w) => w.contributionDays)
    .sort((a, b) => a.date.localeCompare(b.date));

  const today = days[days.length - 1].date;
  let longest = 0, run = 0, active = 0, busiest = days[0];
  for (const d of days) {
    if (d.contributionCount > 0) {
      run += 1;
      active += 1;
      if (run > longest) longest = run;
    } else {
      run = 0;
    }
    if (d.contributionCount > busiest.contributionCount) busiest = d;
  }

  // A streak stays alive on a day with no commits yet, so walk back from the end
  // and only start counting once a contributing day is found.
  let current = 0;
  for (let i = days.length - 1; i >= 0; i--) {
    if (days[i].contributionCount > 0) current += 1;
    else if (!(i === days.length - 1 && days[i].date === today)) break;
  }

  return {
    total: calendar.totalContributions,
    active,
    current,
    longest,
    busiest: busiest.contributionCount,
  };
}

// ---------------------------------------------------------------- render
// A monospace comma occupies a full advance, so 4,773 reads as "4 , 773".
// Tuck it in with negative dx rather than dropping the separator.
const n = (v, size) => {
  const s = v.toLocaleString("en-US");
  const kern = (size * -0.17).toFixed(1);
  return s.replace(/,/g, `</tspan><tspan dx="${kern}">,</tspan><tspan dx="${kern}">`);
};

function svg(p, m, { W, numSize, labSize, cols, height, gap }) {
  const figures = [
    [n(m.total, numSize), "contributions"],
    [n(m.active, numSize), "active days"],
    [n(m.longest, numSize), "longest streak"],
    [n(m.busiest, numSize), "busiest day"],
  ];
  const colW = W / cols;
  const rows = Math.ceil(figures.length / cols);
  const parts = [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${height}" width="${W}" height="${height}" role="img" ` +
      `aria-label="Last 12 months: ${m.total} contributions across ${m.active} active days, ` +
      `longest streak ${m.longest} days, busiest day ${m.busiest} contributions" font-kerning="none">` +
      `<title>Contribution signal, last 12 months</title><style>${FONT_CSS}` +
      `text{font-family:GM,ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre}` +
      `.n{font-weight:600;font-size:${numSize}px;letter-spacing:-.03em;fill:${p.text}}` +
      `.l{font-weight:400;font-size:${labSize}px;fill:${p.dim}}</style>`,
    `<rect width="${W}" height="${height}" fill="${p.bg}"/>`,
  ];
  figures.forEach(([value, label], i) => {
    const col = i % cols, row = (i / cols) | 0;
    const x = col * colW + 1;
    const y = gap + row * (height - gap) / rows;
    if (col > 0) {
      parts.push(`<line x1="${x - 1}" y1="${y - gap + 14}" x2="${x - 1}" y2="${y + labSize + 12}" stroke="${p.line}"/>`);
    }
    parts.push(`<rect x="${x + 18}" y="${y - numSize + 4}" width="2" height="${numSize - 8}" fill="${p.mint}"/>`);
    parts.push(`<text class="n" x="${x + 34}" y="${y}"><tspan>${value}</tspan></text>`);
    parts.push(`<text class="l" x="${x + 34}" y="${y + labSize + 10}">${label}</text>`);
  });
  return parts.join("") + "</svg>";
}

const WIDE = { W: 1200, numSize: 34, labSize: 12.5, cols: 4, height: 104, gap: 56 };
const NARROW = { W: 360, numSize: 26, labSize: 11, cols: 2, height: 132, gap: 46 };

const metrics = measure(await fetchCalendar());
for (const [theme, p] of [["dark", DARK], ["light", LIGHT]]) {
  for (const [suffix, geom] of [["", WIDE], ["-sm", NARROW]]) {
    const file = join(ROOT, "assets", `signal-${theme}${suffix}.svg`);
    writeFileSync(file, svg(p, metrics, geom));
  }
}
console.log(
  `signal: ${metrics.total} contributions, ${metrics.active} active days, ` +
  `current ${metrics.current}, longest ${metrics.longest}, busiest ${metrics.busiest}`,
);
