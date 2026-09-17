"""Verify a built wheel ships the production plugin, never the fake USB plugin."""
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as wheel:
    names = wheel.namelist()
    assert any('/libs/libopenvino_ncs2_plugin.' in name for name in names), 'MYRIAD missing from wheel'
    assert not any('ncs2_test_plugin' in name for name in names), 'Fake USB plugin must not ship'
    assert not any('2022.3' in name for name in names), 'Legacy runtime must not ship'
print('Wheel includes production NCS2 plugin only')
