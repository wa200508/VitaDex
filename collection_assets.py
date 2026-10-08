"""Delete only known private assets after a durable collection change."""
from pathlib import Path


def remove_unused_assets(root, candidates, cards):
    root = Path(root).resolve()
    photos = (root / 'photos').resolve()
    if photos != root / 'photos':
        return []  # A redirected directory is not owned app storage.
    referenced = {
        (root / asset).resolve()
        for card in cards for asset in (card.photo_asset, card.local_art_asset) if asset
    }
    failures = []
    for asset in candidates:
        if not asset:
            continue
        path = (root / asset).resolve()
        if path.parent != photos or path in referenced:
            continue
        try:
            path.unlink(missing_ok=True)
        except OSError:
            failures.append(asset)
    return failures


def remove_orphaned_photos(root, cards, now=None, minimum_age=24 * 60 * 60):
    """Collect only aged, unreferenced files with the app's own UUID naming pattern."""
    import re
    import time
    now = time.time() if now is None else now
    root = Path(root).resolve()
    photos = root / 'photos'
    if photos.resolve() != photos:
        return []
    owned = re.compile(r'(?:[0-9a-f]{32}(?:-art)?\.jpg|picker-[0-9a-f]{32}\.tmp)\Z')
    candidates = []
    try:
        for path in photos.iterdir():
            if not owned.fullmatch(path.name) or path.is_symlink():
                continue
            try:
                if now - path.stat().st_mtime >= minimum_age:
                    candidates.append(str(path.relative_to(root)))
            except OSError:
                continue
    except OSError:
        return []
    return remove_unused_assets(root, candidates, cards)
