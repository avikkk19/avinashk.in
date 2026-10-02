/* Pixel art from character maps. Any <svg data-pixel="name"> is drawn on load;
   Pixel.draw(svg, name) draws on demand.
   Colours: # accent · p currentColor (follows the theme) · others per sprite. */
(() => {
  const SPRITES = {
    // the mascot. w wing · h horn · e eye · f/F fire (only shows while breathing)
    dragon: {
      map: [
        "..........h.h.......",
        ".ww......####.......",
        ".www....##e###ffF...",
        "..wwww.#######fFFFf.",
        "#...wwww#####..ffF..",
        "##..#######.........",
        ".##########.........",
        "...##...##..........",
      ],
      w: 14,
      ink: { "#": "#d9775a", w: "#a5523a", h: "#f1c3a8", e: "#141413", f: "#ff8a1f", F: "#ffd35c" },
    },
    flag: {
      map: [
        "p##pp##p",
        "ppp##pp#",
        "p##pp##p",
        "ppp##pp#",
        "p.......",
        "p.......",
        "p.......",
        "p.......",
      ],
    },
    prompt: {
      map: [
        "ppppppppppp",
        "p.........p",
        "p.#.......p",
        "p..#......p",
        "p.#...###.p",
        "p.........p",
        "ppppppppppp",
      ],
    },
    trophy: {
      map: [
        "p#######p",
        "p#######p",
        ".p#####p.",
        "..#####..",
        "...###...",
        "....#....",
        "...ppp...",
        "..ppppp..",
      ],
    },
    helmet: {
      map: [
        "..#####...",
        ".#######..",
        "#####pppp.",
        "#####pppp#",
        "##########",
        "######....",
        ".#####....",
      ],
    },
    pen: {
      map: [
        "......pp",
        ".....p#p",
        "....p#p.",
        "...p#p..",
        "..p#p...",
        ".ppp....",
        ".pp.....",
        "p.......",
      ],
    },
  };

  function draw(svg, name) {
    const s = SPRITES[name];
    if (!s) return svg;
    const w = s.w || s.map[0].length, h = s.map.length;
    const ink = Object.assign({ "#": "var(--accent, #d9775a)", p: "currentColor" }, s.ink);
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("shape-rendering", "crispEdges");
    let out = "";
    s.map.forEach((row, y) => [...row].forEach((ch, x) => {
      if (!ink[ch]) return;
      const cls = ch === "e" ? ' class="eye"' : ch === "f" || ch === "F" ? ' class="fire"' : "";
      out += `<rect${cls} x="${x}" y="${y}" width="1.02" height="1.02" fill="${ink[ch]}"/>`;
    }));
    svg.innerHTML = out;
    return svg;
  }

  window.Pixel = { draw };
  const auto = () => document.querySelectorAll("svg[data-pixel]").forEach((svg) => draw(svg, svg.dataset.pixel));
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto);
  else auto();
})();
