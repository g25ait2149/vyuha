#!/usr/bin/env python3
"""Produce an ANONYMIZED code artifact of the Vyuha repo for double-blind review
(e.g. upload to https://anonymous.4open.science).

Design (v2, hardened after a v1 audit found leaks the v1 self-check missed):
  * ALLOWLIST, not copy-everything: ship only what a reviewer needs to reproduce the paper
    (package code, eval harness, notebooks, raw scores, analysis tools, reproducibility docs).
    Planning docs, decks, PDFs, previews and legacy dirs are never copied.
  * Binary formats that can carry names in metadata or on title pages (pdf/pptx/docx/xlsx/images)
    are never copied, even inside allowlisted dirs.
  * Every copied file is scrubbed as text (any extension, incl. LICENSE/CITATION.cff/html).
  * A post-scan reads EVERY output file and fails (exit 1) on any identity token, e-mail, or
    API-token-shaped secret (HF hf_..., Groq gsk_...). Review its output before uploading.

    python tools/anonymize_mirror.py --src . --dest /tmp/vyuha_anon

It never modifies the real repo. The paper .tex is anonymised separately via ACL [review] mode.
"""
import argparse, os, re, shutil, sys

# what a reviewer needs; everything else is left out
ALLOW_DIRS = ["vyuha", "eval", "integrations", "service", "tests", "notebooks", "results", "tools"]
ALLOW_FILES = ["README.md", "LICENSE", "pyproject.toml", "requirements.txt", "Makefile", "CITATION.cff",
               "docs/REPRODUCIBILITY.md", "docs/Vyuha_Model_Card.md"]
SKIP_FILES = {"anonymize_mirror.py"}                 # carries the real names in its map by design
SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}
SKIP_DIR_SUBSTR = ("_backup_", "_superseded_", "_prevyuha", "_prereframe")
BINARY_EXT = {".pdf", ".pptx", ".ppt", ".docx", ".doc", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".gif",
              ".zip", ".npy", ".npz", ".pkl", ".bin", ".safetensors", ".pt", ".pth", ".joblib"}

# applied in order (most specific first); values are neutral
REPLACEMENTS = [
    # README provenance paragraph: names a student project + course + institute -> neutral wording
    ("It started as my major project for CSL6010 (Cyber Security) at IIT Jodhpur, built on an\n"
     "earlier jailbreak detector of mine (RJD-v2), and I've kept working on it since.",
     "It builds on an earlier jailbreak detector (RJD-v2)."),
    ("Team RJD, IIT Jodhpur (CSL6010)", "Anonymous Authors"),
    ("U E Sai Pavan Vamshi Krishna, IIT Jodhpur", "Anonymous Author(s)"),
    ("U E Sai Pavan Vamshi Krishna", "Anonymous Author(s)"),
    ("Sai Pavan Vamshi Krishna", "Anonymous Author(s)"),
    ("uekpavanharish@gmail.com", "anon@example.com"),
    ("G25AIT2149", "ANON-ID"),
    ("github.com/g25ait2149/vyuha.git", "anonymous.4open.science/r/vyuha-ANON"),
    ("github.com/g25ait2149/vyuha", "anonymous.4open.science/r/vyuha-ANON"),
    ("github.com/g25ait2149/aegis.git", "anonymous.4open.science/r/vyuha-ANON"),
    ("github.com/g25ait2149/aegis", "anonymous.4open.science/r/vyuha-ANON"),
    ("g25ait2149/vyuha-rjd3-guard", "anon/vyuha-guard-ANON"),
    ("g25ait2149/vyuha", "anon/vyuha-ANON"),
    ("g25ait2149", "anon"),
    ("Indian Institute of Technology Jodhpur", "[Anonymous Institution]"),
    ("IIT Jodhpur", "[Anonymous Institution]"),
    ("IITJ", "[Anonymous Institution]"),
    ("CSL6010", "[course]"),
    ("the professor's question", "a reviewer's question"),
    ("the professor's ask", "a reviewer's ask"),
    ("The professor", "A reviewer"),
    ("the professor", "a reviewer"),
]
CITATION_ANON = """cff-version: 1.2.0
message: "Anonymised for double-blind review. Citation details will be restored at camera-ready."
title: "Vyuha: a layered defense for large language models"
type: software
authors:
  - name: "Anonymous Author(s)"
license: MIT
repository-code: "https://anonymous.4open.science/r/vyuha-ANON"
"""
# post-scan: identity tokens (case-insensitive) + secrets + any e-mail address
LEAK = re.compile(
    r"pavan|vamshi|uekpavan|saipa|g25ait|jodhpur|major project|course project|m\\.tech|\biitj\b|csl6010|"
    r"indian institute of technology|the professor|my professor|"
    r"hf_[A-Za-z0-9]{30,}|gsk_[A-Za-z0-9]{30,}|"
    # real-looking personal/institutional e-mails only (attack fixtures use fake domains like evil.com)
    r"[A-Za-z0-9._%+-]+@(?:gmail|googlemail|yahoo|outlook|hotmail|icloud|proton(?:mail)?)\.[a-z.]{2,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:ac\.in|edu|edu\.in)\b",
    re.IGNORECASE)


def _skip_dir(d):
    return d in SKIP_DIRS or any(s in d for s in SKIP_DIR_SUBSTR)


def _copy(sp, dp, total):
    if os.path.basename(sp).startswith(".fuse_hidden") or os.path.basename(sp) in SKIP_FILES:
        return
    if os.path.splitext(sp)[1].lower() in BINARY_EXT:
        return
    os.makedirs(os.path.dirname(dp), exist_ok=True)
    if os.path.basename(sp) == "CITATION.cff":
        open(dp, "w", encoding="utf-8").write(CITATION_ANON); return
    try:
        txt = open(sp, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return                                        # undecodable -> not shipped (can't be scrubbed)
    for old, new in REPLACEMENTS:
        n = txt.count(old)
        if n:
            txt = txt.replace(old, new); total[old] = total.get(old, 0) + n
    open(dp, "w", encoding="utf-8").write(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".")
    ap.add_argument("--dest", required=True)
    a = ap.parse_args()
    src, dest = os.path.abspath(a.src), os.path.abspath(a.dest)
    if os.path.commonpath([src, dest]) == src:
        sys.exit("dest must be OUTSIDE src (so the real repo is never modified)")
    if os.path.exists(dest):
        shutil.rmtree(dest)
    total = {}
    for f in ALLOW_FILES:
        if os.path.exists(os.path.join(src, f)):
            _copy(os.path.join(src, f), os.path.join(dest, f), total)
    for d in ALLOW_DIRS:
        for root, dirs, files in os.walk(os.path.join(src, d)):
            dirs[:] = [x for x in dirs if not _skip_dir(x)]
            for f in files:
                sp = os.path.join(root, f)
                _copy(sp, os.path.join(dest, os.path.relpath(sp, src)), total)

    open(os.path.join(dest, "REVIEWERS.md"), "w", encoding="utf-8").write(
        "# Anonymous artifact for double-blind review\n\n"
        "This is an anonymised copy of the code, notebooks, raw scores and analysis scripts behind the paper.\n"
        "Notebooks normally `git clone` the repository in their first cell; for review, upload this folder\n"
        "to the notebook environment instead (or unzip it there) and run from its root.\n\n"
        "* CPU-only re-analysis of the guard comparison: `python tools/analyze_guard_scores.py`\n"
        "  (reads `results/guard_scores_v2.csv`; output matches `results/guard_analysis_v2.txt`).\n"
        "* Unit tests: `python -m pytest -q tests`.\n"
        "* Run order, seeds, data sources and model versions: `docs/REPRODUCIBILITY.md`.\n")
    n_files = sum(len(fs) for _, _, fs in os.walk(dest))
    print(f"anonymized artifact -> {dest}  ({n_files} files)")
    for old, _ in REPLACEMENTS:
        if total.get(old):
            print(f"  {total[old]:>4}  {old!r}")
    leaks = []
    for root, _, files in os.walk(dest):
        for f in files:
            p = os.path.join(root, f)
            txt = open(p, "rb").read().decode("utf-8", errors="ignore")
            for m in LEAK.finditer(txt):
                leaks.append((os.path.relpath(p, dest), txt[max(0, m.start() - 40):m.end() + 20].replace("\n", " ")))
    if leaks:
        print(f"\nFAIL - {len(leaks)} potential leak(s); fix the source or REPLACEMENTS, then re-run:")
        for p, ctx in leaks[:60]:
            print(f"  {p}: ...{ctx}...")
        sys.exit(1)
    print("\nCLEAN - full scan of every shipped file: no identity tokens, e-mails or API-token-shaped secrets.")


if __name__ == "__main__":
    main()
