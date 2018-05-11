// Test for OpenSSL Conan package
// Dmitriy Vetutnev, Odant 2018


#include <stdlib.h>


#include <openssl/crypto.h>

#ifdef _WIN32
#include <openssl/applink.c>
#endif


int main(int argc, char** argv) {

#ifdef _WIN32
    OPENSSL_Applink();
#endif

    const char* version = OpenSSL_version(OPENSSL_VERSION);
    printf("OpenSSL version: %s\n", version);

    return EXIT_SUCCESS;
}
