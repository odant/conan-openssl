project(PackageTest C)
cmake_minimum_required(VERSION 3.0)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

find_package(OpenSSL REQUIRED)

if(MSVC)
    add_definitions(-D_CRT_SECURE_NO_DEPRECATE)
    add_definitions(-D_CRT_NONSTDC_NO_DEPRECATE)
endif()

enable_testing()

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
