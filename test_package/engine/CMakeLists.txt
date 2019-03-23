# Test for OpenSSL external engines Conan package
# Dmitriy Vetutnev, ODANT, 2018-2019


project(EngineTest C)
cmake_minimum_required(VERSION 3.5)


# Dummy engine

add_library(external_dummy_engine SHARED 
    dummy.c
)
target_include_directories(external_dummy_engine PRIVATE ${OPENSSL_INCLUDE_DIRS})

add_test(
    NAME "\"Command-line load external dummy engine\""
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    COMMAND openssl engine -t -tt -vvvv -c $<TARGET_FILE:external_dummy_engine>
)

