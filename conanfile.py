from conans import ConanFile, tools
import os, glob


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
        self.options["zlib"].shared=False
        self.options["zlib"].minizip=False
        # DLL sign
        if self.settings.os != "Windows" or not self.options.shared:
            self.options.dll_sign = False
        # Pure C library
        del self.settings.compiler.libcxx

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("strawberryperl/5.26.0@conan/stable")
            self.build_requires("nasm/2.13.01@conan/stable")
            self.build_requires("find_sdk_winxp/[~=1.0]@%s/stable" % self.user)
        if self.options.dll_sign:
            self.build_requires("find_windows_signtool/[~=1.0]@%s/stable" % self.user)
        
    def build(self):
        build_options = "threads"
        build_options += " no-comp"
        build_options += " no-unit-test"
        build_options += " no-hw"
        build_options += " no-dso"
        build_options += " no-dynamic-engine"
        if self.settings.build_type == "Debug":
            build_options += " no-asm"
        if not self.options.shared:
            build_options += " no-shared"
        build_options += " --%s" % str(self.settings.build_type).lower()
        self.output.info("--------------Start build--------------")
        if self.settings.os == "Linux":
            self.unix_build(build_options)
        elif self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.msvc_build(build_options)
        self.output.info("--------------Build done---------------")
        
    def unix_build(self, build_options):
        configure_cmd = os.path.join(self.source_folder, "src", "Configure")
        target = "linux-%s" % self.settings.arch
        self.run("%s %s %s" % (configure_cmd, build_options, target))
        self.run("make build_libs -j %s" % tools.cpu_count())
        
    def msvc_build(self, build_options):
        target = "VC-WIN"
        if self.settings.arch == "x86_64":
            target += "64A"
        else:
            target += "32"
        configure_cmd = "perl " + os.path.join(self.source_folder, "src", "Configure")
        env_vars = tools.vcvars_dict(self.settings, filter_known_paths=False)
        t = str(self.settings.compiler.get_safe("toolset"))
        if t.endswith("_xp"):
            with tools.pythonpath(self):
                import find_sdk_winxp
                env_vars = find_sdk_winxp.dict_append(self.settings.arch, env=env_vars)
        with tools.environment_append(env_vars):
            self.run("set")
            self.run("perl --version")
            self.run("%s %s %s" % (configure_cmd, target, build_options))
            self.run("nmake build_libs")
        # Sign DLL
        if self.options.dll_sign:
            with tools.pythonpath(self):
                from find_windows_signtool import find_signtool
                signtool = '"' + find_signtool(str(self.settings.arch)) + '"'
                params =  "sign /a /t http://timestamp.verisign.com/scripts/timestamp.dll"
                pattern = os.path.join(self.build_folder, "*.dll")
                for fpath in glob.glob(pattern):
                    self.output.info("Sign %s" % fpath)
                    cmd = "{} {} {}".format(signtool, params, fpath)
                    self.run(cmd)
        
    def package(self):
        self.copy("FindOpenSSL.cmake", src=".", dst=".")
        self.copy("*.h", src="src/include/openssl", dst="include/openssl", keep_path=False)
        self.copy("*.h", src="include/openssl", dst="include/openssl", keep_path=False)
        if self.options.shared:
            self.copy("*.so*", dst="lib", keep_path=False, symlinks=True)
        else:
            self.copy("*.a", dst="lib", keep_path=False)
        if self.settings.os == "Windows":
            self.copy("*applink.c", dst="include/openssl", keep_path=False)
            self.copy("libcrypto.lib", src=self.build_folder, dst="lib", keep_path=False)
            self.copy("libssl.lib", src=self.build_folder, dst="lib", keep_path=False)
            self.copy("libcrypto-*.dll", src=self.build_folder, dst="bin", keep_path=False)
            self.copy("libssl-*.dll", src=self.build_folder, dst="bin", keep_path=False)
            self.copy("libcrypto-*.pdb", src=self.build_folder, dst="bin", keep_path=False)
            self.copy("libssl-*.pdb", src=self.build_folder, dst="bin", keep_path=False)

    def package_info(self):
        if self.settings.os == "Linux":
            self.cpp_info.libs = ["ssl", "crypto", "dl", "pthread"]
        elif self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.cpp_info.libs = ["ssl", "crypto", "crypt32", "msi", "ws2_32"]
