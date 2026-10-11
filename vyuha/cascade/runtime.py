"""One place that handles compute-notebook runtime failure modes on EVERY platform. Every long-running notebook
must call persistent_out() for its output dir and finalize() at the end. Rules: docs/Notebook_Robustness_Rules.md.
"""
import os


def persistent_out(name, log=print, require_persistent=True):
    """Return (OUT, kaggle, persistent). Guarantees OUT is on PERSISTENT storage, or loudly warns (and, if
    require_persistent, raises) BEFORE any long compute — so outputs can never be silently lost again.
      - Kaggle: /kaggle/working/<name>; persists ONLY in a committed (Batch) run. In an interactive/draft session
        it is EPHEMERAL -> warn/raise (detected via KAGGLE_KERNEL_RUN_TYPE).
      - Colab: mount Google Drive -> /content/drive/MyDrive/<name>_run (persistent). If mount fails -> warn/raise.
    """
    kaggle = os.path.isdir('/kaggle/working')
    if kaggle:
        rt = os.environ.get('KAGGLE_KERNEL_RUN_TYPE', '')
        persistent = (rt == 'Batch')
        out = f'/kaggle/working/{name}'
        if not persistent:
            msg = (f"Kaggle run type = {rt!r} (not 'Batch'). /kaggle/working is EPHEMERAL in an interactive/draft "
                   f"session and is WIPED on reset. STOP and use Save Version -> Save & Run All (Commit) so outputs "
                   f"persist in the Output tab.")
            log('=' * 78); log('WARNING: ' + msg); log('=' * 78)
            if require_persistent:
                raise RuntimeError(msg + ' (set require_persistent=False to override deliberately)')
    else:
        out = f'/content/{name}'; persistent = False
        try:
            from google.colab import drive
            drive.mount('/content/drive'); out = f'/content/drive/MyDrive/{name}_run'; persistent = True
        except Exception as e:
            log('=' * 78)
            log('WARNING: Google Drive mount FAILED -> /content is EPHEMERAL; a runtime reclaim will wipe outputs. '
                'Mount Drive, or download the moment the run ends. ' + repr(e)[:80])
            log('=' * 78)
            if require_persistent:
                raise RuntimeError('Drive not mounted; outputs would be ephemeral (set require_persistent=False to override)')
    os.makedirs(out, exist_ok=True)
    log(f'OUT = {out}  ({"PERSISTENT" if persistent else "EPHEMERAL - unsafe"})')
    return out, kaggle, persistent


def finalize(outf, kaggle, persistent, log=print):
    """Announce how to retrieve the output, correctly per platform (no Colab-only files.download on Kaggle)."""
    import shutil
    log(f'done: {outf}')
    if kaggle:
        try:
            shutil.copy(outf, '/kaggle/working/' + os.path.basename(outf))
        except Exception:
            pass
        log('KAGGLE: retrieve from the Output tab (/kaggle/working). Only a COMMITTED (Save & Run All) run keeps it.')
    elif persistent:
        log('COLAB: saved to Google Drive (MyDrive). Copy it to Aegis/results/.')
    else:
        try:
            from google.colab import files; files.download(outf)
        except Exception:
            log('EPHEMERAL: download NOW before the runtime ends:', outf)
