from copy import deepcopy

from collection_assets import remove_unused_assets
from database import NATURE_DB


def test_cleanup_retains_shared_and_unowned_files(tmp_path):
    photos = tmp_path / 'photos'
    photos.mkdir()
    shared, unused, outside = photos / 'shared.jpg', photos / 'unused.jpg', tmp_path / 'outside.jpg'
    for path in (shared, unused, outside):
        path.write_bytes(b'image')
    card = deepcopy(NATURE_DB.build_card(next(iter(NATURE_DB.organisms.values()))))
    card.photo_asset = 'photos/shared.jpg'
    assert remove_unused_assets(tmp_path, ['photos/shared.jpg', 'photos/unused.jpg', 'outside.jpg'], [card]) == []
    assert shared.exists()
    assert outside.exists()
    assert not unused.exists()


def test_cleanup_does_not_follow_an_external_symlink(tmp_path):
    root = tmp_path / 'app'
    (root / 'photos').mkdir(parents=True)
    outside = tmp_path / 'outside.jpg'
    outside.write_bytes(b'image')
    (root / 'photos' / 'linked.jpg').symlink_to(outside)
    remove_unused_assets(root, ['photos/linked.jpg'], [])
    assert outside.exists()


def test_orphan_cleanup_keeps_recent_referenced_and_unknown_files(tmp_path):
    import os
    from collection_assets import remove_orphaned_photos
    photos = tmp_path / 'photos'
    photos.mkdir()
    old = photos / ('a' * 32 + '.jpg')
    live = photos / ('b' * 32 + '.jpg')
    recent = photos / ('c' * 32 + '.jpg')
    unknown = photos / 'user-file.jpg'
    for path in (old, live, recent, unknown):
        path.write_bytes(b'image')
        os.utime(path, (0, 0))
    os.utime(recent, (99990, 99990))
    card = deepcopy(NATURE_DB.build_card(next(iter(NATURE_DB.organisms.values()))))
    card.photo_asset = 'photos/' + live.name
    remove_orphaned_photos(tmp_path, [card], now=100000)
    assert not old.exists()
    assert live.exists() and recent.exists() and unknown.exists()


def test_cleanup_rejects_a_redirected_photos_directory(tmp_path):
    from collection_assets import remove_orphaned_photos
    root = tmp_path / 'app'
    root.mkdir()
    outside = tmp_path / 'external'
    outside.mkdir()
    photo = outside / ('a' * 32 + '.jpg')
    photo.write_bytes(b'original')
    (root / 'photos').symlink_to(outside, target_is_directory=True)
    remove_unused_assets(root, ['photos/' + photo.name], [])
    remove_orphaned_photos(root, [], now=10**12)
    assert photo.exists()
