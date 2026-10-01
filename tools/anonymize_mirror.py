#!/usr/bin/env python3
"""Produce an ANONYMIZED copy of the Vyuha repo for double-blind submission
(e.g. an https://anonymous.4open.science mirror).

It never touches the real repo: it copies the tree to a destination dir and rewrites
author-identifying strings in text files to neutral placeholders. Run, then upload the
output dir (or point 4open.science at it).

    python tools/anonymize_mirror.py --src . --dest /tmp/vyuha_anon

Review the printed summary before uploading. The paper .tex is already anonymised via ACL
`[review]` mode, so the submission PDF needs no scrubbing; this is for the CODE artifact.
"""
import argparse, os, re, shutil, sys

# Replacement map, applied in order (most specific first). Values are deliberately neutral.
REPLACEMENTS = [
    ("U E Sai Pavan Vamshi Krishna, IIT Jodhpur", "Anonymous Author(s)"),
    ("U E Sai Pavan Vamshi Krishna", "Anonymous Author(s)"),
    ("Sai Pavan Vamshi Krishna", "Anonymous Author(s)"),
    ("uekpavanharish@gmail.com", "anon@example.com"),
    ("G25AIT2149", "ANON-ID"),
    # repo / model handles and URLs (longest first so the short handle doesn't pre-empt them)
    ("github.com/g25ait2149/vyuha.git", "anonymous.4open.science/r/vyuha-ANON"),
    ("github.com/g25ait2149/vyuha", "anonymous.4open.science/r/vyuha-ANON"),
    ("github.com/g25ait2149/aegis.git", "anonymous.4open.science/r/vyuha-ANON"),
    ("github.com/g25ait2149/aegis", "anonymous.4open.science/r/vyuha-ANON"),
    ("g25ait2149/vyuha-rjd3-guard", "anon/vyuha-guard-ANON"),
    ("g25ait2149/vyuha", "anon/vyuha-ANON"),
    ("g25ait2149", "anon"),
    # affiliation / course identifiers (double-blind). Comment these two out if too aggressive.
    ("IIT Jodhpur", "[Anonymous Institution]"),
    ("CSL6010", "[course]"),
]

TEXT_EXT = {".py", ".md", ".tex", ".ipynb", ".txt", ".toml", ".cfg", ".yaml", ".yml", ".json"}
SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}
# this dev tool carries the real names in its map by design; never ship it in the anonymized mirror
SKIP_FILES = {"anonymize_mirror.py"}
# skip backup/superseded copies so we don't ship duplicates
SKIP_DIR_SUBSTR = ("_backup_", "_superseded_", "_prevyuha", "_prereframe")


def should_skip_dir(name):
    return name in SKIP_DIRS or any(s in name for s in SKIP_DIR_SUBSTR)


def scrub_text(text):
    counts = {}
    for old, new in REPLACEMENTS:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            counts[old] = counts.get(old, 0) + n
    return text, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".")
    ap.add_argument("--dest", required=True)
    args = ap.parse_args()
    src, dest = os.path.abspath(args.src), os.path.abspath(args.dest)
    if os.path.commonpath([src, dest]) == src and dest.startswith(src):
        sys.exit("dest must be OUTSIDE src (so the real repo is never modified)")
    if os.path.exists(dest):
        shutil.rmtree(dest)

    total = {}
    scrubbed_files = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        rel = os.path.relpath(root, src)
        out_root = os.path.join(dest, rel) if rel != "." else dest
        os.makedirs(out_root, exist_ok=True)
        for f in files:
            if f in SKIP_FILES:
                continue
            sp, dp = os.path.join(root, f), os.path.join(out_root, f)
            if os.path.splitext(f)[1].lower() in TEXT_EXT:
                try:
                    txt = open(sp, encoding="utf-8").read()
                except (UnicodeDecodeError, OSError):
                    shutil.copy2(sp, dp); continue
                new, counts = scrub_text(txt)
                open(dp, "w", encoding="utf-8").write(new)
                if counts:
                    scrubbed_files += 1
                    for k, v in counts.items():
                        total[k] = total.get(k, 0) + v
            else:
                shutil.copy2(sp, dp)

    print(f"anonymized copy -> {dest}")
    print(f"files rewritten: {scrubbed_files}")
    print("replacements made:")
    for old, _ in REPLACEMENTS:
        if total.get(old):
            print(f"  {total[old]:>4}  {old!r}")
    # safety re-scan: any identity token left anywhere in the output?
    leak = 0
    pats = re.compile(r"g25ait2149|G25AIT2149|uekpavanharish|Sai Pavan|Vamshi Krishna|IIT Jodhpur|CSL6010")
    for root, dirs, files in os.walk(dest):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        for f in files:
            if os.path.splitext(f)[1].lower() in TEXT_EXT:
                try:
                    if pats.search(open(os.path.join(root, f), encoding="utf-8").read()):
                        leak += 1; print(f"  !! residual identity token in {os.path.relpath(os.path.join(root,f),dest)}")
                except (UnicodeDecodeError, OSError):
                    pass
    print("CLEAN - no residual identity tokens" if not leak else f"WARNING: {leak} file(s) still contain identity tokens")


if __name__ == "__main__":
    main()
