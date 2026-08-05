# ============================================================================
# Vyuha setup via GitHub  -  paste this as the FIRST cell of each notebook.
# No Kaggle dataset needed. Settings -> Internet: ON.  Refresh = git push; re-run.
# ============================================================================
import sys, os, glob, subprocess
REPO_URL = "https://github.com/g25ait2149/vyuha.git"     # <-- set this once
DEST = "/kaggle/working/vyuha_src"

# Private repo? add a GITHUB_TOKEN Kaggle Secret and use:
# from kaggle_secrets import UserSecretsClient
# REPO_URL = f"https://{UserSecretsClient().get_secret('GITHUB_TOKEN')}@github.com/g25ait2149/vyuha.git"

if os.path.isdir(os.path.join(DEST, ".git")):
    subprocess.run(["git", "-C", DEST, "pull", "--ff-only"], check=False)   # already cloned -> update
else:
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, DEST], check=False)

hits = glob.glob(DEST + "/**/vyuha/__init__.py", recursive=True)
root = os.path.dirname(os.path.dirname(hits[0])) if hits else DEST
sys.path.insert(0, root)
for m in [m for m in sys.modules if m == "vyuha" or m.startswith(("vyuha.", "eval"))]:
    del sys.modules[m]                                       # drop cached old modules

import subprocess as _sp; _sp.run("pip -q install datasets transformers torch peft bitsandbytes "
    "accelerate sentence-transformers wandb langdetect 2>/dev/null", shell=True)
print("vyuha repo at:", root)
