# OpenSSL Conan package
# Dmitriy Vetutnev, ODANT, 2018-2019


from conans import ConanFile, tools
from conans.errors import ConanException
import os, glob


def get_safe(options, name):
    try:
        return getattr(options, name, None)
    except ConanException:
        return None


class OpensslConan(ConanFile):
    name = "openssl"
    version = "1.1.1b"
    license = "The current OpenSSL licence is an 'Apache style' license: https://www.openssl.org/source/license.html"
    description = "OpenSSL is an open source project that provides a robust, commercial-grade, and full-featured " \
                  "toolkit for the Transport Layer Security (TLS) and Secure Sockets Layer (SSL) protocols"
    url = "https://github.com/odant/conan-openssl"
    settings = {
        "os": ["Windows", "Linux"],
        "compiler": ["Visual Studio", "gcc"],
        "build_type": ["Debug", "Release"],
        "arch": ["x86_64", "x86", "mips"]
    }
    options = {
        "shared": [False, True],
        "dll_sign": [False, True],
        "with_unit_tests": [False, True],
    }
    default_options = "shared=True", "dll_sign=True", "with_unit_tests=False"
    exports_sources = "src/*", "FindOpenSSL.cmake", "build.patch"
    no_copy_source = True
    build_policy = "missing"

    def configure(self):
        # DLL sign
        if self.settings.os != "Windows" or not self.options.shared:
            del self.options.dll_sign
        # Pure C library
        del self.settings.compiler.libcxx
        # Disable Windows XP support
        toolset = str(self.settings.compiler.get_safe("toolset"))
        if toolset.endswith("_xp"):
            raise Exception("This package is not compatible Windows XP")

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.build_requires("strawberryperl/5.26.0@conan/stable")
            self.build_requires("nasm/2.13.01@conan/stable")
        if get_safe(self.options, "dll_sign"):
            self.build_requires("windows_signtool/[~=1.0]@%s/stable" % self.user)

    def source(self):
        tools.patch(patch_file="build.patch")

    def build(self):
        build_options = []
        build_options.append("threads")
        build_options.append("no-comp") # Disable ZLIB
        build_options.append("enable-engine")
        build_options.append("no-dynamic-engine")
        build_options.append("no-autoload-config")
        #
        if not self.options.shared:
            build_options.append("no-shared")
        #
        if self.options.with_unit_tests:
            build_options.append("enable-unit-test")
        else:
            build_options.append("no-tests")
        #
        if self.settings.build_type == "Debug":
            build_options.append("no-asm")
            build_options.append("--debug")
        else:
            build_options.append("--release")
        #
        self.output.info("--------------Start build--------------")
        if self.settings.os == "Linux":
            self.unix_build(build_options)
        elif self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.msvc_build(build_options)
        self.output.info("--------------Build done---------------")

    def unix_build(self, build_options):
        configure_cmd = "perl " + os.path.join(self.source_folder, "src", "Configure")
        if self.options.shared:
            build_options.append("-Wl,-rpath,'\\$$ORIGIN'")
        target = {
            "x86": "linux-x86",
            "x86_64": "linux-x86_64",
            "mips": "linux-mips32"
        }.get(str(self.settings.arch))
        self.run("%s %s %s" % (configure_cmd, " ".join(build_options), target))
        self.run("make -j %s" % tools.cpu_count())
        if self.options.with_unit_tests:
            self.run("make test")

    def msvc_build(self, build_options):
        configure_cmd = "perl " + os.path.join(self.source_folder, "src", "Configure")
        build_options.append("-D_WIN32_WINNT=0x0601") # Windows 7 and Windows Server 2008 R2 minimal target
        target = {
            "x86": "VC-WIN32",
            "x86_64": "VC-WIN64A"
        }.get(str(self.settings.arch))
        env = tools.vcvars_dict(self.settings, filter_known_paths=False)
        env["LINK"] = "/subsystem:console,6.01" # Windows 7 and Windows Server 2008 R2 minimal target
        # Run build
        with tools.environment_append(env):
            self.run("perl --version")
            self.run("%s %s %s" % (configure_cmd, " ".join(build_options), target))
            self.run("nmake")
            if self.options.with_unit_tests:
                self.run("nmake test")

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
        # Pack application
        self.copy("openssl", dst="bin", src="apps", keep_path=False)
        self.copy("openssl.exe", dst="bin", src="apps", keep_path=False)
        # Sign DLL
        if get_safe(self.options, "dll_sign"):
            import windows_signtool
            patternDLL = os.path.join(self.package_folder, "bin", "*.dll")
            patternEXE = os.path.join(self.package_folder, "bin", "*.exe")
            for fpath in (glob.glob(patternDLL) + glob.glob(patternEXE)):
                fpath = fpath.replace("\\", "/")
                for alg in ["sha1", "sha256"]:
                    is_timestamp = True if self.settings.build_type == "Release" else False
                    cmd = windows_signtool.get_sign_command(fpath, digest_algorithm=alg, timestamp=is_timestamp)
                    self.output.info("Sign %s" % fpath)
                    self.run(cmd)

    def package_id(self):
        self.info.options.with_unit_tests = "any"

    def package_info(self):
        if self.settings.os == "Linux":
            self.cpp_info.libs = ["ssl", "crypto", "dl", "pthread"]
        elif self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.cpp_info.libs = ["libssl", "libcrypto", "crypt32", "msi", "ws2_32"]
            self.cpp_info.defines = ["_CRT_SECURE_NO_WARNINGS"]
