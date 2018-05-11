# OpenSSL Conan package
# Dmitriy Vetutnev, Odant 2018


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
    version = "1.1.0g"
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
    options = {"shared": [False, True], "dll_sign": [False, True]}
    default_options = "shared=True", "dll_sign=True"
    exports_sources = "src/*", "FindOpenSSL.cmake"
    no_copy_source = True
    build_policy = "missing"
        
    def configure(self):
        # DLL sign
        if self.settings.os != "Windows" or not self.options.shared:
            del self.options.dll_sign
        # Pure C library
        del self.settings.compiler.libcxx

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.build_requires("strawberryperl/5.26.0@conan/stable")
            self.build_requires("nasm/2.13.01@conan/stable")
            self.build_requires("get_vcvars/[~=1.0]@%s/stable" % self.user)
            self.build_requires("find_sdk_winxp/[~=1.0]@%s/stable" % self.user)
        if get_safe(self.options, "dll_sign"):
            self.build_requires("windows_signtool/[~=1.0]@%s/stable" % self.user)
        
    def build(self):
        build_options = []
        build_options.append("threads")
        build_options.append("no-comp")
        build_options.append("no-unit-test")
        build_options.append("no-hw")
        build_options.append("no-dso")
        build_options.append("no-dynamic-engine")
        if self.settings.build_type == "Debug":
            build_options.append("no-asm")
        if not self.options.shared:
            build_options.append("no-shared")
        build_options.append("--%s" % str(self.settings.build_type).lower())
        self.output.info("--------------Start build--------------")
        if self.settings.os == "Linux":
            self.unix_build(build_options)
        elif self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.msvc_build(build_options)
        self.output.info("--------------Build done---------------")
        
    def unix_build(self, build_options):
        configure_cmd = "perl " + os.path.join(self.source_folder, "src", "Configure")
        target = {
            "x86": "linux-x86",
            "x86_64": "linux-x86_64",
            "mips": "linux-mips32"
        }.get(str(self.settings.arch))
        self.run("%s %s %s" % (configure_cmd, " ".join(build_options), target))
        self.run("make build_libs -j %s" % tools.cpu_count())
        
    def msvc_build(self, build_options):
        target = "VC-WIN"
        if self.settings.arch == "x86_64":
            target += "64A"
        else:
            target += "32"
        configure_cmd = "perl " + os.path.join(self.source_folder, "src", "Configure")
        env = tools.vcvars_dict(self.settings, filter_known_paths=False, force=True)
        toolset = str(self.settings.compiler.get_safe("toolset"))
        if toolset.endswith("_xp"):
            import find_sdk_winxp
            env = find_sdk_winxp.dict_append(self.settings.arch, env=env)
        # Run build
        with tools.environment_append(env):
            self.run("set")
            self.run("perl --version")
            self.run("%s %s %s" % (configure_cmd, " ".join(build_options), target))
            self.run("nmake build_libs")
        
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
        # Sign DLL
        if get_safe(self.options, "dll_sign"):
            import windows_signtool
            pattern = os.path.join(self.package_folder, "bin", "*.dll")
            for fpath in glob.glob(pattern):
                fpath = fpath.replace("\\", "/")
                for alg in ["sha1", "sha256"]:
                    is_timestamp = True if self.settings.build_type == "Release" else False
                    cmd = windows_signtool.get_sign_command(fpath, digest_algorithm=alg, timestamp=is_timestamp)
                    self.output.info("Sign %s" % fpath)
                    self.run(cmd)

    def package_info(self):
        if self.settings.os == "Linux":
            self.cpp_info.libs = ["ssl", "crypto", "dl", "pthread"]
        elif self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self.cpp_info.libs = ["libssl", "libcrypto", "crypt32", "msi", "ws2_32"]
            self.cpp_info.defines = ["_CRT_SECURE_NO_WARNINGS"]
