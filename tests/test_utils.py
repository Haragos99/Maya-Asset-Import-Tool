# tests/test_utils.py
import os
import hashlib
from pathlib import Path
import time
import tempfile

from asset_nav_panel.utils import flat_thumbnail_name

def test_flat_thumbnail_name_is_deterministic():
    p = r"C:\assets\characters\hero\model.obj"
    name1 = flat_thumbnail_name(p)+".png"
    name2 = flat_thumbnail_name(p)+".png"
    assert name1 == name2
    assert name1.endswith(".png")


def test_flat_thumbnail_name_handles_various_paths():
    paths = [
        r":\assets\characters\hero\model.obj",
        r"assets/characters/hero/model.obj",
        r"assets\characters\hero\model.obj",
    ]
    names = set()
    for p in paths:
        name = flat_thumbnail_name(p)+".png"
        names.add(name)
    # All variations should produce the same flattened name
    assert len(names) == 1

