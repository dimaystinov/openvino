# SPDX-License-Identifier: Apache-2.0
if(NOT ENABLE_INTEL_MYRIAD)
    return()
endif()
if(NOT BUILD_SHARED_LIBS OR NOT (LINUX OR APPLE))
    message(FATAL_ERROR "NCS2 currently requires a shared-library Linux or macOS build")
endif()

add_subdirectory(thirdparty)
set(TARGET_NAME openvino_ncs2_plugin)
ov_add_plugin(NAME ${TARGET_NAME}
              DEVICE_NAME MYRIAD
              SOURCES src/plugin.cpp src/blob.hpp src/transport.hpp
              VERSION_DEFINES_FOR src/plugin.cpp)
target_link_libraries(${TARGET_NAME} PRIVATE ncs2_mvnc)
if(LINUX)
    # mvnc/XLink cannot safely be unloaded while process-wide transport threads exist.
    target_link_options(${TARGET_NAME} PRIVATE "-Wl,-z,nodelete")
endif()

if(ENABLE_MYRIAD_NCS2_TESTS)
    add_executable(ncs2_blob_tests tests/blob_tests.cpp)
    target_include_directories(ncs2_blob_tests PRIVATE src)
    add_test(NAME ncs2_blob_parser COMMAND ncs2_blob_tests)

    ov_add_plugin(NAME openvino_ncs2_test_plugin DEVICE_NAME MYRIAD_TEST
                  SOURCES src/plugin.cpp tests/fake_mvnc.cpp
                  VERSION_DEFINES_FOR src/plugin.cpp
                  SKIP_INSTALL SKIP_REGISTRATION)
    target_compile_definitions(openvino_ncs2_test_plugin PRIVATE NCS2_TEST_TRANSPORT)
    target_include_directories(openvino_ncs2_test_plugin PRIVATE src thirdparty/mvnc/include)
    if(NOT CMAKE_CROSSCOMPILING)
        find_package(Python3 REQUIRED COMPONENTS Interpreter)
        # Set this to the matching built Python package, never a different wheel ABI.
        set(NCS2_TEST_PYTHONPATH "" CACHE PATH "Directory containing the built openvino Python package")
        if(NCS2_TEST_PYTHONPATH)
            add_test(NAME ncs2_plugin_integration
                COMMAND ${CMAKE_COMMAND} -E env "PYTHONPATH=${NCS2_TEST_PYTHONPATH}"
                ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_plugin.py
                $<TARGET_FILE:openvino_ncs2_test_plugin>)
            add_test(NAME ncs2_plugin_registration
                COMMAND ${CMAKE_COMMAND} -E env "PYTHONPATH=${NCS2_TEST_PYTHONPATH}"
                ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_registration.py)
        endif()
    endif()
endif()
