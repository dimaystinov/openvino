# SPDX-License-Identifier: Apache-2.0
# Isolated builds of the vendored 2022.3.2 USB transport. No old runtime/compiler.
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(NCS2_LIBUSB REQUIRED IMPORTED_TARGET libusb-1.0)

file(GLOB xlink_sources CONFIGURE_DEPENDS
     XLink/pc/*.c XLink/pc/protocols/*.c)
file(GLOB_RECURSE xlink_shared CONFIGURE_DEPENDS XLink/shared/*.c)
list(APPEND xlink_sources ${xlink_shared} XLink/pc/MacOS/pthread_semaphore.c)
add_library(ncs2_xlink STATIC ${xlink_sources})
target_include_directories(ncs2_xlink PUBLIC XLink/shared/include XLink/pc/protocols
                           PRIVATE XLink/pc/MacOS)
target_link_libraries(ncs2_xlink PRIVATE PkgConfig::NCS2_LIBUSB Threads::Threads)

add_library(ncs2_mvnc STATIC
    mvnc/src/mvnc_api.c mvnc/src/mvnc_data.c
    mvnc/src/watchdog/watchdog.cpp mvnc/src/watchdog/xlink_device.cpp)
target_include_directories(ncs2_mvnc PUBLIC mvnc/include mvnc/include/watchdog
                           PRIVATE XLink/pc/MacOS)
target_link_libraries(ncs2_mvnc PRIVATE ncs2_xlink Threads::Threads ${CMAKE_DL_LIBS})
foreach(target IN ITEMS ncs2_mvnc ncs2_xlink)
    set_target_properties(${target} PROPERTIES POSITION_INDEPENDENT_CODE ON
        C_VISIBILITY_PRESET hidden CXX_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN ON COMPILE_WARNING_AS_ERROR OFF)
    target_compile_definitions(${target} PRIVATE
        __PC__ HAVE_STRUCT_TIMESPEC _CRT_SECURE_NO_WARNINGS USE_USB_VSC XLINK_USE_BUS)
    if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
        target_compile_definitions(${target} PRIVATE _GNU_SOURCE)
    endif()
endforeach()
