from conans import ConanFile
import os


class OpensslConan(ConanFile):
    name = "openssl"
    version = "1.1.0g"
    license = "The current OpenSSL licence is an 'Apache style' license: https://www.openssl.org/source/license.html"
    description = "OpenSSL is an open source project that provides a robust, commercial-grade, and full-featured " \
                  "toolkit for the Transport Layer Security (TLS) and Secure Sockets Layer (SSL) protocols"
    url = "https://github.com/odant/conan-openssl"
    settings = {
        "os": ["Windows", "Linux"],
        "compiler": ["Visual Studio", "gcc"],
        "build_type": ["Debug", "Release"],
        "arch": ["x86_64", "x86"]
    }
    options = {"shared": [False, True], "dll_sign": [False, True]}
    default_options = "shared=True", "dll_sign=True"
    exports_sources = "src/*"
    no_copy_source = True
    build_policy = "missing"
    
    def configure(self):
        # DLL sign
        if self.settings.os != "Windows" or not self.options.shared:
            self.options.dll_sign = False
        # Position indepent
        #if self.settings.os == "Windows":
        #    self.options.fPIC = False
        #elif self.options.shared:
        #    self.options.fPIC = True
        # Pure C library
        del self.settings.compiler.libcxx

    def build(self):
        build_options = "threads"
        build_options += " no-zlib-dynamic"
        if not self.options.shared:
            build_options += " no-shared"
        build_options += " --%s" % str(self.settings.build_type).lower()
        build_options += " --prefix=%s" % self.package_folder
        self.output.info("--------------Start build--------------")
        if self.settings.os == "Linux":
            self.unix_build(build_options)
        elif self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.msvc_build(build_options)
        self.output.info("--------------Build done---------------")
        
    def unix_build(self, build_options):
        if self.options.shared:
            build_options += r" -Wl,-rpath=\$ORIGIN"
        configure_cmd = os.path.join(self.source_folder, "src", "Configure")
        target = "linux-%s" % self.settings.arch
        self.run("%s %s %s" % (configure_cmd, build_options, target))
        self.run("make")
        self.run("make install")
        
    def msvc_build(self, build_options):
        pass
