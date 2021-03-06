/* 
 * Test for OpenSSL Conan package
 * Dmitriy Vetutnev, ODANT, 2018-2019
*/


#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <string.h>

#include <openssl/evp.h>
#include <openssl/aes.h>
#include <openssl/err.h>

#ifdef _WIN32
#include <openssl/applink.c>
#endif


char password[16];
char data[1024];

void cleanUp(char*, EVP_CIPHER_CTX*, char*, EVP_CIPHER_CTX*);

int main(int argc, char** argv) {

#ifdef _WIN32
    OPENSSL_Applink();
#endif

    printf("data length: %zd bytes, password length: %zd bytes\n", sizeof(data), sizeof(password));

    srand((unsigned int) time(NULL));

    for (int i = 0; i < sizeof(password); i++) {
        password[i] = (char) rand();
    }

    for (int i = 0; i < sizeof(data); i++) {
        data[i] = (char) rand();
    }


/* Genarate key and initisl vector. Init cipher context. */

    char* e_data = NULL;
    char* d_data = NULL;
    EVP_CIPHER_CTX* e_ctx = NULL;
    EVP_CIPHER_CTX* d_ctx = NULL;

    int res;

    const int nrounds = 5;
    char key[32], iv[32];
    res = EVP_BytesToKey(EVP_aes_256_cbc(), EVP_sha1(), NULL, password, sizeof(password), nrounds, key, iv);
    if (res != 32) {
        printf("Key size is %d bits - should be 256 bits\n", res * 8);
        exit(EXIT_FAILURE);
    }

    e_ctx = EVP_CIPHER_CTX_new();
    if (e_ctx == NULL) {
        printf("Allocate encrypt context failed\n");
        exit(EXIT_FAILURE);
    }
    res = EVP_EncryptInit_ex(e_ctx, EVP_aes_256_cbc(), NULL, key, iv);
    if (res == 0) {
        unsigned long err_code = ERR_get_error();
        printf("Init encrypt context failed, code: %ld, error: %s\n", err_code, ERR_error_string(err_code, NULL));
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }

    d_ctx = EVP_CIPHER_CTX_new();
    if (e_ctx == NULL) {
        printf("Allocate decrypt context failed\n");
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }
    res = EVP_DecryptInit_ex(d_ctx, EVP_aes_256_cbc(), NULL, key, iv);
    if (res == 0) {
        unsigned long err_code = ERR_get_error();
        printf("Init decrypt context failed, code: %ld, error: %s\n", err_code, ERR_error_string(err_code, NULL));
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }


/* Encrypt/decrypt */

    int e_data_len = sizeof(data) + AES_BLOCK_SIZE;
    e_data = malloc(e_data_len);
    if (e_data == NULL) {
        printf("Allocate buffer for encrypt data failed\n");
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }

    res = EVP_EncryptUpdate(e_ctx, e_data, &e_data_len, data, sizeof(data));
    if (res == 0) {
        unsigned long err_code = ERR_get_error();
        printf("EVP_EncryptUpdate() failed, code: %ld, error: %s\n", err_code, ERR_error_string(err_code, NULL));
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }
    printf("EVP_EncryptUpdate() encrypted %d bytes\n", e_data_len);

    int e_data_tail_len = 0;
    res = EVP_EncryptFinal_ex(e_ctx, e_data + e_data_len, &e_data_tail_len);
    if (res == 0) {
        unsigned long err_code = ERR_get_error();
        printf("EVP_EncryptFinal_ex() failed, code: %ld, error: %s\n", err_code, ERR_error_string(err_code, NULL));
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }
    printf("EVP_EncryptFinal_ex() encrypted %d bytes\n", e_data_tail_len);
    e_data_len += e_data_tail_len;
    printf("Amount encrypted %d bytes\n", e_data_len);

    int d_data_len = e_data_len;
    d_data = malloc(d_data_len);
    if (d_data == NULL) {
        printf("Allocate buffer for decrypt data failed\n");
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }

    res = EVP_DecryptUpdate(d_ctx, d_data, &d_data_len, e_data, e_data_len);
    if (res == 0) {
        unsigned long err_code = ERR_get_error();
        printf("EVP_DecryptUpdate() failed, code: %ld, error: %s\n", err_code, ERR_error_string(err_code, NULL));
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }
    printf("EVP_DecryptUpdate() decrypted %d bytes\n", d_data_len);

    int d_data_tail_len = 0;
    res = EVP_DecryptFinal_ex(d_ctx, d_data + d_data_len, &d_data_tail_len);
    if (res == 0) {
        unsigned long err_code = ERR_get_error();
        printf("EVP_DecryptFinal_ex() failed, code: %ld, error: %s\n", err_code, ERR_error_string(err_code, NULL));
        free(e_data);
        free(d_data);
        EVP_CIPHER_CTX_free(e_ctx);
        EVP_CIPHER_CTX_free(d_ctx);
        exit(EXIT_FAILURE);
    }
    printf("EVP_DecryptFinal_ex() encrypted %d bytes\n", d_data_tail_len);
    d_data_len += d_data_tail_len;
    printf("Amount decrypted %d bytes\n", d_data_len);


/* Compare */

    if (d_data_len != sizeof(data)) {
        printf("Decrypted data length not equal source data length, d_data_len: %d, sizeof(data): %zd\n", d_data_len, sizeof(data));
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }

    if (memcmp(data, d_data, sizeof(data)) != 0) {
        printf("Decrypted data not equal source data\n");
        cleanUp(e_data, e_ctx, d_data, d_ctx);
        exit(EXIT_FAILURE);
    }

    printf("Encrypt/decrypt OK");


/* Clean */

    cleanUp(e_data, e_ctx, d_data, d_ctx);
    return EXIT_SUCCESS;
}

void cleanUp(char* e_data, EVP_CIPHER_CTX* e_ctx, char* d_data, EVP_CIPHER_CTX* d_ctx) {

    if (e_data != NULL) {
        free(e_data);
    }

    if (e_ctx != NULL) {
        EVP_CIPHER_CTX_free(e_ctx);
    }

    if (d_data != NULL) {
        free(d_data);
    }

    if (d_ctx != NULL) {
        EVP_CIPHER_CTX_free(d_ctx);
    }

}
