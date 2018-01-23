#include <stdlib.h>
#include <stdio.h>

#include <openssl/crypto.h>

int main(int argc, char** argv) {
    const char* version = OpenSSL_version(OPENSSL_VERSION);
    printf("version => %s\n", version);
    return EXIT_SUCCESS;
}
