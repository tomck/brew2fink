import urllib.request
from pathlib import Path
from macpkg_migrate_core import Identity, candidates_for, load_snapshot

DEFAULT_URL="https://tomck.github.io/macpkg-catalog/catalog.json"
DEFAULT_CACHE="~/.cache/brew2fink/macpkg-catalog.json"

def load(path):
    """Load a pinned snapshot through the shared manager-neutral core."""
    return load_snapshot(Path(path).expanduser())

def fetch(cache=DEFAULT_CACHE,refresh=False,url=DEFAULT_URL,progress=None):
    path=Path(cache).expanduser()
    if path.exists() and not refresh: return load(path)
    if progress: progress("Downloading the published macpkg-catalog relationships...")
    request=urllib.request.Request(url,headers={"User-Agent":"brew2fink"})
    with urllib.request.urlopen(request,timeout=120) as response: data=response.read()
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    return load(path)


def candidates(snapshot, kind, name):
    """Return Fink candidates while preserving all catalog relation metadata."""
    source = Identity("homebrew", "formula" if kind == "formula" else "cask", name)
    return [candidate for candidate in candidates_for(snapshot.get("relations", []), source) if candidate.target.manager == "fink"]
