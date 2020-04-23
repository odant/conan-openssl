# Test for OpenSSL Conan package
# Dmitriy Vetutnev, ODANT, 2018-2020


project(PackageTest C CXX)
cmake_minimum_required(VERSION 3.5)

option(DISABLE_TEST_ENGINE "Disable test dymanic load engine" OFF)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

if(UNIX)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELWITHDEBINFO ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_MINSIZEREL ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
endif()

enable_testing()

# CONAN_PKG::openssl imported targets

add_executable(test_openssl_CONAN_PKG test_openssl.c)
target_link_libraries(test_openssl_CONAN_PKG CONAN_PKG::openssl)
set_target_properties(test_openssl_CONAN_PKG
    PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH True
)
add_test(
    NAME test_openssl_CONAN_PKG
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND test_openssl_CONAN_PKG
)

# Normal imported targets

find_package(OpenSSL REQUIRED)

add_executable(test_openssl test_openssl.c)
target_link_libraries(test_openssl OpenSSL::SSL)
set_target_properties(test_openssl
    PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH True
)
add_test(
    NAME test_openssl
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND test_openssl
)

add_executable(test_crypto test_crypto.c)
target_link_libraries(test_crypto OpenSSL::Crypto)
set_target_properties(test_crypto
    PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH True
)
add_test(
    NAME test_crypto
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND test_crypto
)

# Test application

add_test(
    NAME "\"Application OpenSSL\""
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND ${CMAKE_BINARY_DIR}/bin/openssl version
)

# Tests engine
if (NOT DISABLE_TEST_ENGINE)
    add_subdirectory(engine)
endif()

