cmake_minimum_required(VERSION 3.20)

project(FocusReaderWindows VERSION 0.1.0 LANGUAGES C RC)

if(NOT WIN32)
    message(FATAL_ERROR "FocusReader.Windows is a native Win32 application.")
endif()

set(FOCUSREADER_VERSION "${PROJECT_VERSION}" CACHE STRING "FocusReader release version")
if(NOT FOCUSREADER_VERSION MATCHES "^[0-9]+\\.[0-9]+\\.[0-9]+$")
    message(FATAL_ERROR "FOCUSREADER_VERSION must use MAJOR.MINOR.PATCH.")
endif()

string(REPLACE "." ";" FOCUSREADER_VERSION_PARTS "${FOCUSREADER_VERSION}")
list(GET FOCUSREADER_VERSION_PARTS 0 FOCUSREADER_VERSION_MAJOR)
list(GET FOCUSREADER_VERSION_PARTS 1 FOCUSREADER_VERSION_MINOR)
list(GET FOCUSREADER_VERSION_PARTS 2 FOCUSREADER_VERSION_PATCH)

file(TO_CMAKE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/resources/app.manifest" FOCUSREADER_MANIFEST_PATH)
configure_file(
    resources/focusreader.rc.in
    ${CMAKE_CURRENT_BINARY_DIR}/focusreader.rc
    @ONLY)

set(FOCUSREADER_RESOURCE_SOURCES ${CMAKE_CURRENT_BINARY_DIR}/focusreader.rc)
if(NOT MSVC)
    configure_file(
        resources/manifest.rc.in
        ${CMAKE_CURRENT_BINARY_DIR}/manifest.rc
        @ONLY)
    list(APPEND FOCUSREADER_RESOURCE_SOURCES ${CMAKE_CURRENT_BINARY_DIR}/manifest.rc)
endif()

add_library(focusreader_core STATIC src/core.c)
target_include_directories(focusreader_core PUBLIC include)
target_compile_features(focusreader_core PUBLIC c_std_17)

add_executable(
    FocusReader.Windows
    WIN32
    src/main.c
    ${FOCUSREADER_RESOURCE_SOURCES})
target_compile_features(FocusReader.Windows PRIVATE c_std_17)
target_compile_definitions(
    FocusReader.Windows
    PRIVATE
    UNICODE
    _UNICODE
    _CRT_SECURE_NO_WARNINGS
    WIN32_LEAN_AND_MEAN
    NOMINMAX)
target_link_libraries(
    FocusReader.Windows
    PRIVATE
    focusreader_core
    user32
    gdi32
    shell32
    comctl32
    comdlg32)

add_executable(FocusReader.Windows.Checks tests/test_core.c)
target_compile_features(FocusReader.Windows.Checks PRIVATE c_std_17)
target_link_libraries(FocusReader.Windows.Checks PRIVATE focusreader_core)

if(MSVC)
    target_link_options(
        FocusReader.Windows
        PRIVATE
        "/MANIFEST:EMBED"
        "/MANIFESTINPUT:${FOCUSREADER_MANIFEST_PATH}")
    target_compile_options(focusreader_core PRIVATE /W4 /permissive-)
    target_compile_options(FocusReader.Windows PRIVATE /W4 /permissive-)
    target_compile_options(FocusReader.Windows.Checks PRIVATE /W4 /permissive-)
else()
    target_compile_options(focusreader_core PRIVATE -Wall -Wextra -Wpedantic)
    target_compile_options(FocusReader.Windows PRIVATE -Wall -Wextra -Wpedantic)
    target_compile_options(FocusReader.Windows.Checks PRIVATE -Wall -Wextra -Wpedantic)
    target_link_options(FocusReader.Windows PRIVATE -static -static-libgcc)
    target_link_options(FocusReader.Windows.Checks PRIVATE -static -static-libgcc)
endif()

set_target_properties(
    FocusReader.Windows
    FocusReader.Windows.Checks
    PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

foreach(configuration Debug Release RelWithDebInfo MinSizeRel)
    string(TOUPPER "${configuration}" configuration_upper)
    set_target_properties(
        FocusReader.Windows
        FocusReader.Windows.Checks
        PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY_${configuration_upper} "${CMAKE_BINARY_DIR}/bin")
endforeach()

enable_testing()
add_test(NAME focusreader_native_checks COMMAND FocusReader.Windows.Checks)
