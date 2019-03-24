/* 
 * Test for OpenSSL external engine Conan package
 * Fake rand engine, generate monotone sequence
 * https://www.openssl.org/blog/blog/2015/10/08/engine-building-lesson-1-a-minimum-useless-engine/
 * https://github.com/engine-corner/Lesson-1-A-useless-example
 * Dmitriy Vetutnev, ODANT, 2018-2019
*/


#include <stdio.h>

#include <openssl/engine.h>
#include <openssl/rand.h>


static unsigned char nextVal = 0;
static unsigned char getNextVal() {
    const unsigned char ret = nextVal;
    if (nextVal + 1 <= 255) {
        nextVal++;
    }
    else {
        nextVal = 0;
    }
    return ret;
}


static int fakerandBytes(unsigned char* buffer, int length) {
    if (length < 0 ) {
        return 0;
    }
    for (int i = 0; i < length; i++) {
        *buffer++ = getNextVal();
    }
    return length;
}


static RAND_METHOD randMethod = {
    NULL,                       /* seed */
    fakerandBytes,
    NULL,                       /* cleanup */
    NULL,                       /* add */
    fakerandBytes,
    NULL,                       /* status */
};


static const char* engineID = "fakerand";
static const char* engineName = "A fake random generator engine. Generate monotone sequence";


static int fakerandBind(ENGINE* e, const char* id) {
    printf("Called fakerandBind\n");

    static int loaded = 0;
    if (loaded) {
        fprintf(stderr, "dummy engine already loaded\n");
        return 0;
    }

    if (!ENGINE_set_id(e, engineID)) {
        fprintf(stderr, "ENGINE_set_id failed\n");
        return 0;
    }
    if (!ENGINE_set_name(e, engineName)) {
        fprintf(stderr, "ENGINE_set_name failed\n");
        return 0;
    }
    if (!ENGINE_set_RAND(e, &randMethod)) {
        fprintf(stderr, "ENGINE_set_RAND failed\n");
        return 0;
    }
    if (!ENGINE_set_default(e, ENGINE_METHOD_RAND)) {
        fprintf(stderr, "ENGINE_set_default(e, ENGINE_METHOD_RAND failed\n");
        return 0;
    }

    printf("Done fakerandBind\n");
    return 1;
}

IMPLEMENT_DYNAMIC_BIND_FN(fakerandBind)
IMPLEMENT_DYNAMIC_CHECK_FN()

