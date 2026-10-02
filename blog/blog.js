/* Blog behaviour: post tree + progress rail, share links, J/K jumps,
   reading time, the post list on /blog/, and prev/next links. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fmtDate = (iso) => new Date(iso + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const loadPosts = () => fetch("/blog/posts.json").then((r) => r.json()).catch(() => []);

  /* ── Keyboard nav shared by every blog page ───────── */
  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey || e.target.closest("input, textarea")) return;
    const k = e.key.toLowerCase();
    if (k === "h") location.href = "/";
    else if (k === "b") location.href = "/blog/";
    else if (k === "r") location.href = "/resume/";
    else if (k === "t") location.href = "/#term";
    else if ((k === "j" || k === "k") && heads.length) {
      e.preventDefault();
      const i = current();
      const next = k === "j" ? Math.min(heads.length - 1, i + 1) : Math.max(0, i - 1);
      heads[next].scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" });
    }
  });

  /* ── Blog index ──────────────────────────────────── */
  const list = $("#post-list");
  if (list) loadPosts().then((posts) => {
    list.innerHTML = posts.map((p) =>
      `<li><a href="/blog/${p.slug}/"><span class="d">${fmtDate(p.date)}</span><span class="t">${p.title}</span><span class="m">${p.minutes} min</span></a></li>`
    ).join("") || '<li class="d">No posts yet.</li>';
  });

  /* ── Post page ───────────────────────────────────── */
  const article = $("article");
  const heads = article ? [...article.querySelectorAll("h2, h3")] : [];
  if (!article) return;

  const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const tree = $("#tree");
  const links = heads.map((h) => {
    h.id ||= slug(h.textContent);
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = "#" + h.id;
    a.textContent = h.textContent;
    if (h.tagName === "H3") a.className = "sub";
    li.appendChild(a);
    tree.appendChild(li);
    return a;
  });

  const words = article.textContent.trim().split(/\s+/).length;
  const reading = $("[data-reading]");
  if (reading) reading.textContent = Math.max(1, Math.round(words / 220)) + " min";

  // which heading the reader is in: the last one above 30% of the viewport
  function current() {
    let i = 0;
    heads.forEach((h, n) => { if (h.getBoundingClientRect().top < innerHeight * 0.3) i = n; });
    return i;
  }

  const bar = $("#bar"), title = $(".rail-title"), head = $(".post-head");
  const CELLS = 22;
  function update() {
    const r = article.getBoundingClientRect();
    const total = r.height - innerHeight * 0.6;
    const pct = Math.round(Math.min(1, Math.max(0, -r.top / Math.max(1, total))) * 100);
    const n = Math.round((pct / 100) * CELLS);
    bar.innerHTML = `<b>${"▓".repeat(n)}</b>${"░".repeat(CELLS - n)}  ${String(pct).padStart(2, "0")}%`;
    const i = current();
    links.forEach((a, n) => a.classList.toggle("on", n === i && r.top < innerHeight * 0.3));
    title.classList.toggle("on", head.getBoundingClientRect().bottom < 0);
  }
  let queued = false;
  addEventListener("scroll", () => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; update(); }); } }, { passive: true });
  addEventListener("resize", update);
  update();

  /* ── Share ───────────────────────────────────────── */
  const url = location.href.split("#")[0];
  const name = $("h1").textContent;
  $("#share-x").href = "https://x.com/intent/post?text=" + encodeURIComponent(name) + "&url=" + encodeURIComponent(url);
  $("#share-li").href = "https://www.linkedin.com/sharing/share-offsite/?url=" + encodeURIComponent(url);
  $("#share-mail").href = "mailto:?subject=" + encodeURIComponent(name) + "&body=" + encodeURIComponent(url);

  const flash = (btn, text) => {
    const was = btn.textContent;
    btn.textContent = text;
    setTimeout(() => { btn.textContent = was; }, 1400);
  };
  const copy = (btn, text) => navigator.clipboard.writeText(text).then(() => flash(btn, "Copied"), () => flash(btn, "Couldn't copy"));
  $("#copy-url").addEventListener("click", (e) => copy(e.currentTarget, url));
  $("#copy-md").addEventListener("click", (e) => copy(e.currentTarget, "# " + name + "\n\n" + toMarkdown(article)));

  // Enough markdown for these posts: headings, paragraphs, lists, code, links, emphasis.
  function toMarkdown(root) {
    const inline = (n) => [...n.childNodes].map((c) => {
      if (c.nodeType === 3) return c.textContent.replace(/\s+/g, " ");
      const t = c.tagName;
      if (t === "CODE") return "`" + c.textContent + "`";
      if (t === "A") return `[${inline(c)}](${c.href})`;
      if (t === "STRONG" || t === "B") return `**${inline(c)}**`;
      if (t === "EM" || t === "I") return `*${inline(c)}*`;
      return inline(c);
    }).join("");
    return [...root.children].map((el) => {
      const t = el.tagName;
      if (t === "H2") return "## " + el.textContent;
      if (t === "H3") return "### " + el.textContent;
      if (t === "PRE") return "```\n" + el.textContent.replace(/\n$/, "") + "\n```";
      if (t === "UL") return [...el.children].map((li) => "- " + inline(li).trim()).join("\n");
      if (t === "OL") return [...el.children].map((li, i) => `${i + 1}. ` + inline(li).trim()).join("\n");
      if (t === "NAV") return "";
      return inline(el).trim();
    }).filter(Boolean).join("\n\n");
  }

  /* ── Previous / next ─────────────────────────────── */
  const nav = $(".post-nav");
  if (nav) loadPosts().then((posts) => {
    const here = location.pathname.replace(/\/$/, "").split("/").pop();
    const i = posts.findIndex((p) => p.slug === here);
    const newer = posts[i - 1], older = posts[i + 1];
    nav.innerHTML =
      (older ? `<a href="/blog/${older.slug}/">← ${older.title}</a>` : '<a href="/blog/">← All posts</a>') +
      (newer ? `<a href="/blog/${newer.slug}/">${newer.title} →</a>` : '<a href="/">Home →</a>');
  });
})();
