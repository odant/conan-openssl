# Test for OpenSSL external engines Conan package
# Dmitriy Vetutnev, ODANT, 2018-2019


project(EngineTest C)
cmake_minimum_required(VERSION 3.5)


# Dummy engine

add_library(external_dummy_engine SHARED dummy.c)
target_link_libraries(external_dummy_engine OpenSSL::Crypto)

add_test(
    NAME "\"Command-line load external dummy engine\""
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND ${CMAKE_BINARY_DIR}/bin/openssl engine -t -tt -vvvv -c $<TARGET_FILE:external_dummy_engine>
)

# Fake random generator engine

add_library(external_fakerand_engine SHARED fakerand.c)
target_link_libraries(external_fakerand_engine OpenSSL::Crypto)

add_test(
    NAME "\"Command-line load external fake random engine\""
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND ${CMAKE_BINARY_DIR}/bin/openssl rand -engine $<TARGET_FILE:external_fakerand_engine> -hex 10
)

