# OpenSSL Conan package
# Dmitriy Vetutnev, ODANT, 2018-2019


set(OPENSSL_INCLUDE_DIR ${CONAN_INCLUDE_DIRS_OPENSSL})

function(from_hex HEX DEC)
  string(TOUPPER "${HEX}" HEX)
  set(_res 0)
  string(LENGTH "${HEX}" _strlen)

  while (_strlen GREATER 0)
    math(EXPR _res "${_res} * 16")
    string(SUBSTRING "${HEX}" 0 1 NIBBLE)
    string(SUBSTRING "${HEX}" 1 -1 HEX)
    if (NIBBLE STREQUAL "A")
      math(EXPR _res "${_res} + 10")
    elseif (NIBBLE STREQUAL "B")
      math(EXPR _res "${_res} + 11")
    elseif (NIBBLE STREQUAL "C")
      math(EXPR _res "${_res} + 12")
    elseif (NIBBLE STREQUAL "D")
      math(EXPR _res "${_res} + 13")
    elseif (NIBBLE STREQUAL "E")
      math(EXPR _res "${_res} + 14")
    elseif (NIBBLE STREQUAL "F")
      math(EXPR _res "${_res} + 15")
    else()
      math(EXPR _res "${_res} + ${NIBBLE}")
    endif()

    string(LENGTH "${HEX}" _strlen)
  endwhile()

  set(${DEC} ${_res} PARENT_SCOPE)
endfunction()

if(OPENSSL_INCLUDE_DIR AND EXISTS "${OPENSSL_INCLUDE_DIR}/openssl/opensslv.h")
    file(STRINGS "${OPENSSL_INCLUDE_DIR}/openssl/opensslv.h" DEFINE_OPENSSL_MAJOR_VERSION REGEX "^[ \\t]*#[ \\t]*define[ \\t]+OPENSSL_VERSION_MAJOR[ \\t]+")
    string(REGEX REPLACE "^[ \\t]*#[ \\t]*define[ \\t]+OPENSSL_VERSION_MAJOR[ \\t]+([0-9]+).*$" "\\1" OPENSSL_VERSION_MAJOR "${DEFINE_OPENSSL_MAJOR_VERSION}")

    file(STRINGS "${OPENSSL_INCLUDE_DIR}/openssl/opensslv.h" DEFINE_OPENSSL_MINOR_VERSION REGEX "^[ \\t]*#[ \\t]*define[ \\t]+OPENSSL_VERSION_MINOR[ \\t]+")
    string(REGEX REPLACE "^[ \\t]*#[ \\t]*define[ \\t]+OPENSSL_VERSION_MINOR[ \\t]+([0-9]+).*$" "\\1" OPENSSL_VERSION_MINOR "${DEFINE_OPENSSL_MINOR_VERSION}")

    file(STRINGS "${OPENSSL_INCLUDE_DIR}/openssl/opensslv.h" DEFINE_OPENSSL_PATCH_VERSION REGEX "^[ \\t]*#[ \\t]*define[ \\t]+OPENSSL_VERSION_PATCH[ \\t]+")
    string(REGEX REPLACE "^[ \\t]*#[ \\t]*define[ \\t]+OPENSSL_VERSION_PATCH[ \\t]+([0-9]+).*$" "\\1" OPENSSL_VERSION_PATCH "${DEFINE_OPENSSL_PATCH_VERSION}")

    set(OPENSSL_VERSION_STRING "${OPENSSL_VERSION_MAJOR}.${OPENSSL_VERSION_MINOR}.${OPENSSL_VERSION_PATCH}")
    set(OPENSSL_VERSION ${OPENSSL_VERSION_STRING})
    set(OPENSSL_VERSION_COUNT 3)
endif ()

find_library(OPENSSL_CRYPTO_LIBRARY
    NAMES crypto libcrypto
    PATHS ${CONAN_LIB_DIRS_OPENSSL}
    NO_DEFAULT_PATH
)

find_library(OPENSSL_SSL_LIBRARY
    NAMES ssl libssl
    PATHS ${CONAN_LIB_DIRS_OPENSSL}
    NO_DEFAULT_PATH
)

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(OpenSSL
    REQUIRED_VARS
        OPENSSL_CRYPTO_LIBRARY
        OPENSSL_SSL_LIBRARY
        OPENSSL_INCLUDE_DIR
    VERSION_VAR
        OPENSSL_VERSION
)

if(OPENSSL_FOUND)

    include(CMakeFindDependencyMacro)
    find_dependency(Threads)

    if(NOT TARGET OpenSSL::Crypto)
        add_library(OpenSSL::Crypto UNKNOWN IMPORTED)
        set_target_properties(OpenSSL::Crypto PROPERTIES
            INTERFACE_INCLUDE_DIRECTORIES "${OPENSSL_INCLUDE_DIR}"
            IMPORTED_LINK_INTERFACE_LANGUAGES "C"
            IMPORTED_LOCATION "${OPENSSL_CRYPTO_LIBRARY}"
            INTERFACE_COMPILE_DEFINITIONS "${CONAN_COMPILE_DEFINITIONS_OPENSSL}"
            INTERFACE_LINK_LIBRARIES Threads::Threads
        )
    endif()

    if(UNIX)
        set_property(TARGET OpenSSL::Crypto
            APPEND PROPERTY INTERFACE_LINK_LIBRARIES ${CMAKE_DL_LIBS}
        )
    endif()

    if(WIN32)
        set_property(TARGET OpenSSL::Crypto
            APPEND PROPERTY INTERFACE_LINK_LIBRARIES "crypt32" "ws2_32"
        )
    endif()


    if(NOT TARGET OpenSSL::SSL)
        add_library(OpenSSL::SSL UNKNOWN IMPORTED)
        set_target_properties(OpenSSL::SSL PROPERTIES
            INTERFACE_INCLUDE_DIRECTORIES "${OPENSSL_INCLUDE_DIR}"
            IMPORTED_LINK_INTERFACE_LANGUAGES "C"
            IMPORTED_LOCATION "${OPENSSL_SSL_LIBRARY}"
            INTERFACE_LINK_LIBRARIES OpenSSL::Crypto
        )
    endif()

    set(OPENSSL_INCLUDE_DIRS ${OPENSSL_INCLUDE_DIR})
    set(OPENSSL_LIBRARIES ${OPENSSL_SSL_LIBRARY} ${OPENSSL_CRYPTO_LIBRARY})
    set(OPENSSL_DEFINITIONS ${CONAN_COMPILE_DEFINITIONS_OPENSSL})

    mark_as_advanced(OPENSSL_INCLUDE_DIR OPENSSL_LIBRARIES)

endif()

