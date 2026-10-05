import struct

import pytest

from scripts.verify_apk import check_elf


def elf(machine, suffix=b''):
    raw = bytearray(20)
    raw[:4] = b'\x7fELF'
    raw[5] = 1
    raw[18:20] = struct.pack('<H', machine)
    return bytes(raw) + suffix


def test_host_extensions_rejected_even_when_architecture_matches():
    with pytest.raises(ValueError, match='architecture'):
        check_elf(elf(62), 'md.so', 'arm64-v8a')
    with pytest.raises(ValueError, match='glibc'):
        check_elf(elf(62, b'libc.so.6\x00'), 'md.so', 'x86_64')
    check_elf(elf(183), 'android.so', 'arm64-v8a')
    check_elf(elf(62), 'android.so', 'x86_64')
