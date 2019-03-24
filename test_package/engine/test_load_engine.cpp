/* 
 * Test for OpenSSL external engine Conan package
 * Load fake rand engine through openssl.conf
 * Dmitriy Vetutnev, ODANT, 2018-2019
*/


#include <openssl/conf.h>
#include <openssl/err.h>
#include <openssl/rand.h>
#include <openssl/engine.h>

#include <iostream>
#include <cstdlib>
#include <vector>


template<typename CharT, typename Traits>
std::basic_ostream<CharT, Traits>& operator<< (std::basic_ostream<CharT, Traits>& os, const std::vector<unsigned char>& vec) {
    os << '{';
    auto it = std::cbegin(vec);
    const auto endIt = std::cend(vec);
    for(;;) {
        if (it != endIt) {
            os << static_cast<unsigned int>(*it);
        }
        else {
            os << '}';
            break;
        }
        ++it;
        if (it != endIt) {
            os << ',';
        }
    }
    return os;
}


int main(int argc, char* argv[]) {
    std::cout << "Test load fake rand engine through openssl.conf" << std::endl;
    if (argc < 2) {
        std::cout << "Usage: " << std::endl << argv[0] << " path/openssl.conf" << std::endl;
        return EXIT_FAILURE;
    }

    //::OPENSSL_config(NULL);
    ::OpenSSL_add_all_algorithms();
    ::ERR_load_crypto_strings();
    ::ENGINE_load_builtin_engines();
    //::ENGINE_register_all_complete();
    ::ENGINE_add_conf_module();

    std::cout << "OpenSSL config: " << argv[1] << std::endl;
    if (::CONF_modules_load_file(argv[1], "openssl_conf", 0) <= 0) {
        std::cerr << "CONF_modules_load_file failed" << std::endl;
        const char* filename;
        int line;
        ::ERR_get_error_line(&filename, &line);
        std::cerr << filename << ':' << line << std::endl;
        const auto e = ::ERR_get_error();
        char str[4096];
        ::ERR_error_string_n(e, str, sizeof(str));
        std::cerr << str << std::endl;
        return EXIT_FAILURE;
    }

    const std::vector<unsigned char> normalResult = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
    std::vector<unsigned char> result = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

    if (!RAND_bytes(result.data(), result.size())) {
        std::cerr << "RAND_bytes failed" << std::endl;
        const char* filename;
        int line;
        ::ERR_get_error_line(&filename, &line);
        std::cerr << filename << ':' << line << std::endl;
        const auto e = ::ERR_get_error();
        char str[4096];
        ::ERR_error_string_n(e, str, sizeof(str));
        std::cerr << str << std::endl;
        return EXIT_FAILURE;
    }

    std::cout << "normalResult:" << std::endl << normalResult << std::endl;
    std::cout << "result:" << std::endl << result << std::endl;

    if (result != normalResult) {
        std::cout << "Random generator do not take monotone sequence. Engine fakerand not loaded?" << std::endl;
        return EXIT_FAILURE;
    }

    std::cout << "Ok" << std::endl;
    return EXIT_SUCCESS;
}

