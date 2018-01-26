from conans import ConanFile, tools
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
    exports_sources = "src/*", "FindOpenSSL.cmake"
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

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("strawberryperl/5.26.0@conan/stable")
            self.build_requires("nasm/2.13.01@conan/stable")
        
    def build(self):
        build_options = "threads"
        build_options += " no-zlib-dynamic"
        build_options += " no-unit-test"
        build_options += " no-hw"
        build_options += " no-dso"
        build_options += " no-dynamic-engine"
        if not self.options.shared:
            build_options += " no-shared"
        build_options += " --%s" % str(self.settings.build_type).lower()
        #build_options += " --prefix=%s" % self.package_folder
        self.output.info("--------------Start build--------------")
        if self.settings.os == "Linux":
            self.unix_build(build_options)
        elif self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.msvc_build(build_options)
        self.output.info("--------------Build done---------------")
        
    def unix_build(self, build_options):
#        if self.options.shared:
#            build_options += r' -Wl,-rpath,"\$\$$\ORIGIN"'
        configure_cmd = os.path.join(self.source_folder, "src", "Configure")
        target = "linux-%s" % self.settings.arch
        #with tools.environment_append({"LDFLAGS": r" -Wl,-rpath='\$\$ORIGIN' "}):
        self.run("%s %s %s" % (configure_cmd, build_options, target))
        self.run("make build_libs -j %s" % tools.cpu_count())
        #self.run("make")
        #self.run("make install_sw")
        
    def msvc_build(self, build_options):
        vcvars = tools.vcvars_command(self.settings)
        target = "VC-WIN%s" % "64A" if self.settings.arch == "x86_64" else "32"
        configure_cmd = "perl " + os.path.join(self.source_folder, "src", "Configure")
        self.run("%s && %s %s %s" % (vcvars, configure_cmd, target, build_options))
        self.run("%s && %s" % (vcvars, "nmake"))
        
    def package(self):
        self.copy("FindOpenSSL.cmake", src=".", dst=".")
        self.copy("*.h", src="src/include/openssl", dst="include/openssl", keep_path=False)
        self.copy("*.h", src="include/openssl", dst="include/openssl", keep_path=False)
        if self.options.shared:
            self.copy("*.so*", dst="lib", keep_path=False)
        else:
            self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        pass
