# Vendored NCS2 USB transport

`mvnc/` and `XLink/` are copied without source changes from OpenVINO 2022.3.2,
commit `e2c7e4d7b4d6b315c0b62a22438146b28d15f1ee`, paths
`src/plugins/intel_myriad/third_party/{mvnc,XLink}`.
Original per-file copyright/SPDX notices are retained; Apache-2.0 is in the
repository root LICENSE. The original CMake files are retained for provenance
but not executed: the parent CMakeLists builds isolated `ncs2_*` targets.

Only the USB transport and watchdog are linked. No legacy OpenVINO runtime,
Python bindings, graph compiler, model or firmware binary is bundled here.
Firmware and model integration are documented in the plugin README.
The supported build targets are Linux (including CM4) and macOS for host tests.
