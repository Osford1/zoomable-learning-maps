# Owner to-dos

Bullets are for Chen Bin; each one says what is needed, why it blocks, and where.

- **Rebuild the worked example against a public paper.** The map that exists was charted from a paper I
  do not have the authors' permission to republish, so the whole example directory was excluded from this
  repo and the paper is not named anywhere in it. Once a paper under CC-BY or CC0 is picked, rebuild the
  pages against it (1 master + its zooms) and publish that set under `examples/`. Why it blocks: without
  it, `examples/` holds only invented demo content and a reader cannot check the method against a real
  source. Where: `examples/`, and the "Worked example (not published)" section of `README.md`.
- **Do not restate the excluded example's bibliographic claims anywhere.** The removed pages asserted a
  DOI, an acceptance date and an author list that were never checked against the published record. If that
  map is ever published, verify all three first. Why: an unchecked DOI in a public repo is exactly the
  kind of claim this repo forbids. Where: nowhere in the repo today — keep it that way.
- **If written clearance ever arrives from the paper's authors, the excluded example can be re-added.**
  That needs an explicit yes from the corresponding author and the first author, since the pages break
  that paper's method and results down in detail. Why: it is someone else's in-press work. Where: a new
  `examples/<topic>/` folder.
- **Decide the canonical home against `hermes-skills`.** This standalone repo carries the full README and
  the examples, so it is the recommended canonical copy, with `hermes-skills` linking here instead of
  holding a second copy of `SKILL.md`. Why: otherwise the same skill is maintained twice. Where: the
  `hermes-skills` repo plan, and the "Companion skills" wording in `README.md` (the sibling skills are
  currently credited by name with no link, because that repo does not exist yet).
- **Get the upstream repo URL and copyright line for the `diagram-design` skill, or leave it out.**
  Re-vendoring `scripts/self_check.py` and `assets/template-motion.html` under `vendor/diagram-design/`
  requires that project's own `LICENSE` file and a named copyright holder, which the skill does not ship.
  Why: MIT redistribution needs the copyright notice. Where: `CREDITS.md` and "The static gate (not
  bundled)" in `README.md` both state the gate is external until then. If it is re-vendored, the gate can
  run again and the three-command check becomes self-contained.
- **Add the two README screenshots.** List, contents and suggested sizes: `docs/screenshots/README.md`.
  Why: a repo about charts with no chart on the landing page undersells it, and the README currently
  carries only a marked TODO comment rather than a broken image link. Where: `docs/screenshots/`.
- **Decide whether the public repo carries a `v1.0.0` tag.** The `SKILL.md` frontmatter says `1.0.0`.
  Why: the README claims "finished at v1.0.0", and that claim should match a tag. Where: the git tag, then
  `README.md`.
- **Nothing to install for the repo's own checks.** Recorded here so it is not re-investigated: the two
  generators, `verify_links.py` and `audit_headless.py` all run on the Python standard library, and the
  pixel audit runs under Chrome or Edge that is already on this machine. The only optional dependency is
  PyMuPDF, and only when the source document is a PDF.
