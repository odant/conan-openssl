# Test for OpenSSL external engines Conan package
# Dmitriy Vetutnev, ODANT, 2018-2019


project(EngineTest C CXX)
cmake_minimum_required(VERSION 3.5)


# Dummy engine

add_library(dummy_engine SHARED dummy.c)
target_link_libraries(dummy_engine OpenSSL::Crypto)
if(MSVC AND CMAKE_GENERATOR STREQUAL "Ninja")
    target_compile_definitions(dummy_engine PRIVATE _WINDLL)
endif()

add_test(
    NAME "\"Command-line load external dummy engine\""
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND ${CMAKE_BINARY_DIR}/bin/openssl engine -t -tt -vvvv -c $<TARGET_FILE:dummy_engine>
)

# Fake random generator engine

add_library(fakerand_engine SHARED fakerand.c)
target_link_libraries(fakerand_engine OpenSSL::Crypto)
if(MSVC AND CMAKE_GENERATOR STREQUAL "Ninja")
    target_compile_definitions(fakerand_engine PRIVATE _WINDLL)
endif()

add_test(
    NAME "\"Command-line load external fake random engine\""
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND ${CMAKE_BINARY_DIR}/bin/openssl rand -engine $<TARGET_FILE:fakerand_engine> -hex 10
)

# Load fake random generator engine through openssl.conf

if(UNIX)
    set(FAKERAND_PATH ${CMAKE_BINARY_DIR}/bin/libfakerand_engine.so)
else()
    set(FAKERAND_PATH ${CMAKE_BINARY_DIR}/bin/fakerand_engine.dll)
endif()
configure_file(
    fakerand_openssl.conf.in
    ${CMAKE_BINARY_DIR}/bin/fakerand_openssl.conf
    ESCAPE_QUOTES
)

add_executable(test_load_engine test_load_engine.cpp)
target_link_libraries(test_load_engine OpenSSL::Crypto)
set_target_properties(test_load_engine
    PROPERTIES
    INSTALL_RPATH "$ORIGIN"
    BUILD_WITH_INSTALL_RPATH True
)
add_dependencies(test_load_engine fakerand_engine)

add_test(
    NAME test_load_engine
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND test_load_engine ${CMAKE_BINARY_DIR}/bin/fakerand_openssl.conf
)

