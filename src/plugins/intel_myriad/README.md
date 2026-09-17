# Intel Neural Compute Stick 2 / MYRIAD

See [the fork build and integration guide](../../../README_NCS2_RU.md).

Enable with `-DENABLE_INTEL_MYRIAD=ON` (off by default). This is a native
modern OpenVINO plugin for importing static MYRIAD 6.0 blobs; it does not
compile XML/ONNX graphs. Source-vendored mvnc/XLink provides USB transport
without linking the old OpenVINO runtime or using old Python bindings.

The production target is `openvino_ncs2_plugin`, registered as `MYRIAD`.
Tests are opt-in through `ENABLE_MYRIAD_NCS2_TESTS`; the fake USB plugin is
never installed or registered as a production device. Linux/CM4 builds need
libusb in the target sysroot and matching runtime/Python ABI. Hardware
inference is not yet verified in this development environment.
