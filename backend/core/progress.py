"""
Shared model-loading status, polled by the frontend via /settings/status.

Also hooks huggingface_hub's download progress bars so STT/translation model
downloads (the slow part of loading) report real byte-level progress instead
of just a static "loading" label. This covers faster-whisper and transformers
too, since both download through huggingface_hub under the hood.
"""
from functools import lru_cache

status = {
    "stage": "idle",       # "idle" | "loading" | "ready" | "error"
    "target": None,        # human-readable description of what's being loaded
    "bytes_downloaded": None,
    "bytes_total": None,
    "error": None,
}

def set_status(stage: str, target: str = None, error: str = None):
    status["stage"] = stage
    status["target"] = target
    status["error"] = error
    status["bytes_downloaded"] = None
    status["bytes_total"] = None

def _set_progress(downloaded: int, total: int | None):
    status["bytes_downloaded"] = downloaded
    status["bytes_total"] = total

@lru_cache
def install_download_progress_hook():
    """Monkey-patches huggingface_hub's tqdm so any file download during a
    model load reports into `status`. Idempotent (lru_cache ensures this
    runs at most once per process)."""
    # Must patch the actual submodule object (not the `tqdm` class re-exported
    # by huggingface_hub.utils's __init__.py, which shadows the same name at
    # the package level) so we affect the module-level name that
    # _get_progress_bar_context actually resolves at call time. Pulling it
    # from sys.modules sidesteps the attribute-chain shadowing: `import
    # huggingface_hub.utils.tqdm as x` would resolve `x` to the shadowed class
    # instead of the submodule.
    import sys
    import huggingface_hub.utils.tqdm  # ensure it's imported/registered
    hf_tqdm_module = sys.modules["huggingface_hub.utils.tqdm"]

    base_tqdm = hf_tqdm_module.tqdm

    class ProgressReportingTqdm(base_tqdm):
        def __init__(self, *args, **kwargs):
            # Only byte-based download bars are relevant; ignore other tqdm
            # usages (e.g. iterating file lists) that don't set unit="B".
            # tqdm doesn't store `unit` as a readable instance attribute, so
            # we track it ourselves before delegating to the real __init__
            # (which immediately calls update() internally if initial > 0).
            self._reports_progress = kwargs.get("unit") == "B"
            super().__init__(*args, **kwargs)
            if self._reports_progress:
                _set_progress(self.n or 0, self.total)

        def update(self, n=1):
            result = super().update(n)
            if getattr(self, "_reports_progress", False):
                _set_progress(self.n, self.total)
            return result

        def close(self):
            if getattr(self, "_reports_progress", False):
                _set_progress(self.n, self.total)
            super().close()

    hf_tqdm_module.tqdm = ProgressReportingTqdm
