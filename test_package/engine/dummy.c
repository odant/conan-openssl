/* 
 * Test for OpenSSL external engine Conan package
 * Dummy engine
 * https://www.openssl.org/blog/blog/2015/10/08/engine-building-lesson-1-a-minimum-useless-engine/
 * https://github.com/engine-corner/Lesson-1-A-useless-example
 * Dmitriy Vetutnev, ODANT, 2018-2019
*/


#include <stdio.h>

#include <openssl/engine.h>


static const char* engine_id = "dummy";
static const char* engine_name = "A dummy engine for demonstration purposes";


static int bind(ENGINE* e, const char* id) {
    if (!ENGINE_set_id(e, engine_id)) {
        printf("ENGINE_set_id failed\n");
        return 0;
    }
    if (!ENGINE_set_name(e, engine_name)) {
        printf("ENGINE_set_name failed\n");
        return 0;
    }

    return 1;
}

IMPLEMENT_DYNAMIC_BIND_FN(bind)
IMPLEMENT_DYNAMIC_CHECK_FN()

