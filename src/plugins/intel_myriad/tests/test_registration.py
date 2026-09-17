"""Checks the production plugin is discoverable without register_plugin().

No NCS2 is required. This is not a physical inference test.
"""
import openvino as ov

core = ov.Core()
version = core.get_versions('MYRIAD')['MYRIAD']
assert version.description == 'NCS2 native blob plugin', version
properties = {str(p) for p in core.get_property('MYRIAD', 'SUPPORTED_PROPERTIES')}
assert {'AVAILABLE_DEVICES', 'NCS2_FIRMWARE_DIR', 'DEVICE_ID'} <= properties
# Enumeration is meaningful even when the returned device list is empty.
devices = core.get_property('MYRIAD', 'AVAILABLE_DEVICES')
assert isinstance(devices, list)
print('Production MYRIAD auto-registration: OK; devices:', devices)
