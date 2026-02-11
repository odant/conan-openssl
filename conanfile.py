# OpenSSL Conan package
# Dmitriy Vetutnev, ODANT, 2018-2020
# Arkady Yudintsev, ODANT, 2021-2025

from conan import ConanFile, tools
import os, glob, textwrap


class OpensslConan(ConanFile):
    name = "openssl"
    version = "3.0.19+0"
    license = "The current OpenSSL licence is an 'Apache style' license: https://www.openssl.org/source/license.html"
    description = "OpenSSL is an open source project that provides a robust, commercial-grade, and full-featured " \
                  "toolkit for the Transport Layer Security (TLS) and Secure Sockets Layer (SSL) protocols"
    url = "https://github.com/odant/conan-openssl"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [False, True],
        "dll_sign": [False, True],
        "with_unit_tests": [False, True],
    }
    default_options = { 
        "shared": True, 
        "dll_sign": True,
        "with_unit_tests": False
    }
    exports_sources = "src/*", "build.patch", "legacy_provider_static_linkage.patch"
    #no_copy_source = True
    build_policy = "missing"
    package_type = "library"
    python_requires = "windows_signtool/[>=1.2]@odant/stable"

    def configure(self):
        # DLL sign
        if self.settings.os != "Windows" or not self.options.shared:
            del self.options.dll_sign
        # Pure C library
        self.settings.compiler.rm_safe("libcxx")
        self.settings.compiler.rm_safe("cppstd")

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("strawberryperl/[>=5.32.0.0]")
            self.build_requires("nasm/[>=2.16.01]")

    def source(self):
        tools.files.patch(self, patch_file="build.patch")
        tools.files.patch(self, patch_file="legacy_provider_static_linkage.patch")
        
    def generate(self):
        benv = tools.env.VirtualBuildEnv(self)
        benv.generate()
        renv = tools.env.VirtualRunEnv(self)
        renv.generate()
        if tools.microsoft.is_msvc(self):
            vc = tools.microsoft.VCVars(self)
            vc.generate()

    def build(self):
        build_options = []
        build_options.append("no-comp") # Disable ZLIB (possible CRIME attack)
        build_options.append("enable-engine")
        build_options.append("no-autoload-config")
        #
        if not self.options.shared:
            build_options.append("no-shared")
        #
        if self.options.with_unit_tests:
            build_options.append("enable-unit-test")
            build_options.append("enable-buildtest-c++")
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
        elif self.settings.os == "Windows" and (self.settings.compiler == "msvc" or (self.settings.compiler == "clang" and self.settings.compiler.runtime_version)):
            self.msvc_build(build_options)
        self.output.info("--------------Build done---------------")

    def unix_build(self, build_options):
        configure_cmd = "perl " + os.path.join(self.source_folder, "src", "Configure")
        if self.options.shared:
            build_options.append("-Wl,-rpath,'\\$$ORIGIN:\\$$ORIGIN/../lib'")
        target = {
            "x86": "linux-x86",
            "x86_64": "linux-x86_64",
            "mips": "linux-mips32",
            "armv7": "linux-armv4"
        }.get(str(self.settings.arch))
        self.run("%s %s %s" % (configure_cmd, " ".join(build_options), target))
        self.run("make -j %s" % tools.build.build_jobs(self))
        if self.options.with_unit_tests:
            self.run("make test")

    def msvc_build(self, build_options):
        configure_cmd = "perl " + os.path.join(self.source_folder, "src", "Configure")
        build_options.append("-D_WIN32_WINNT=0x0601") # Windows 7 and Windows Server 2008 R2 minimal target
        if self.settings.compiler == "msvc":
            target = {
                "x86": "VC-WIN32",
                "x86_64": "VC-WIN64A"
            }.get(str(self.settings.arch))
        else:    
            target = {
                "x86": "VC-WIN32-CLANGCL",
                "x86_64": "VC-WIN64A-CLANGCL"
            }.get(str(self.settings.arch))
        env = tools.env.Environment()
        env.append("LINK", "/subsystem:console,6.01")
        # Run build
        with env.vars(self).apply():
            self.run("perl --version")
            cmd = "%s %s %s" % (configure_cmd, " ".join(build_options), target)
            self.output.info(cmd)
            self.run(cmd)
            self.run("nmake")
            if self.options.with_unit_tests:
                self.run("nmake test")

    def package(self):
        tools.files.copy(self, "*.h", src=os.path.join(self.build_folder, "src", "include", "openssl"), dst=os.path.join(self.package_folder, "include", "openssl"), keep_path=False, excludes="__DECC_INCLUDE_*")
        tools.files.copy(self, "*.h", src=os.path.join(self.build_folder, "include", "openssl"), dst=os.path.join(self.package_folder, "include", "openssl"), keep_path=False)
        if self.options.shared:
            tools.files.copy(self, "libcrypto.so*", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
            tools.files.copy(self, "libssl.so*", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        else:
            tools.files.copy(self, "*.a", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        if self.settings.os == "Windows":
            tools.files.copy(self, "*applink.c", src=os.path.join(self.source_folder, "src", "ms"), dst=os.path.join(self.package_folder, "include", "openssl"), keep_path=False)
            tools.files.copy(self, "libcrypto.lib", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
            tools.files.copy(self, "libssl.lib", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
            tools.files.copy(self, "libcrypto-*.dll", src=self.build_folder, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
            tools.files.copy(self, "libssl-*.dll", src=self.build_folder, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
            tools.files.copy(self, "libcrypto-*.pdb", src=self.build_folder, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
            tools.files.copy(self, "libssl-*.pdb", src=self.build_folder, dst=os.path.join(self.package_folder, "bin"), keep_path=False)

        self._create_cmake_module_variables(
            os.path.join(self.package_folder, self._module_file_rel_path)
        )
        # Pack application
        tools.files.copy(self, "openssl", dst=os.path.join(self.package_folder, "bin"), src=os.path.join(self.build_folder, "apps"), keep_path=False)
        tools.files.copy(self, "openssl.exe", dst=os.path.join(self.package_folder, "bin"), src=os.path.join(self.build_folder, "apps"), keep_path=False)
        # Sign DLL
        if self.options.get_safe("dll_sign"):
            self.python_requires["windows_signtool"].module.sign(self, [os.path.join(self.package_folder, "bin", "*.dll"), os.path.join(self.package_folder, "bin", "*.exe")])

    def _create_cmake_module_variables(self, module_file):
        content = textwrap.dedent("""\
            set(OPENSSL_FOUND TRUE)
            if(DEFINED OpenSSL_INCLUDE_DIR)
                set(OPENSSL_INCLUDE_DIR ${OpenSSL_INCLUDE_DIR})
            endif()
            if(DEFINED OpenSSL_Crypto_LIBS)
                set(OPENSSL_CRYPTO_LIBRARY ${OpenSSL_Crypto_LIBS})
                set(OPENSSL_CRYPTO_LIBRARIES ${OpenSSL_Crypto_LIBS}
                                             ${OpenSSL_Crypto_DEPENDENCIES}
                                             ${OpenSSL_Crypto_FRAMEWORKS}
                                             ${OpenSSL_Crypto_SYSTEM_LIBS})
            elseif(DEFINED openssl_OpenSSL_Crypto_LIBS_%(config)s)
                set(OPENSSL_CRYPTO_LIBRARY ${openssl_OpenSSL_Crypto_LIBS_%(config)s})
                set(OPENSSL_CRYPTO_LIBRARIES ${openssl_OpenSSL_Crypto_LIBS_%(config)s}
                                             ${openssl_OpenSSL_Crypto_DEPENDENCIES_%(config)s}
                                             ${openssl_OpenSSL_Crypto_FRAMEWORKS_%(config)s}
                                             ${openssl_OpenSSL_Crypto_SYSTEM_LIBS_%(config)s})
            endif()
            if(DEFINED OpenSSL_SSL_LIBS)
                set(OPENSSL_SSL_LIBRARY ${OpenSSL_SSL_LIBS})
                set(OPENSSL_SSL_LIBRARIES ${OpenSSL_SSL_LIBS}
                                          ${OpenSSL_SSL_DEPENDENCIES}
                                          ${OpenSSL_SSL_FRAMEWORKS}
                                          ${OpenSSL_SSL_SYSTEM_LIBS})
            elseif(DEFINED openssl_OpenSSL_SSL_LIBS_%(config)s)
                set(OPENSSL_SSL_LIBRARY ${openssl_OpenSSL_SSL_LIBS_%(config)s})
                set(OPENSSL_SSL_LIBRARIES ${openssl_OpenSSL_SSL_LIBS_%(config)s}
                                          ${openssl_OpenSSL_SSL_DEPENDENCIES_%(config)s}
                                          ${openssl_OpenSSL_SSL_FRAMEWORKS_%(config)s}
                                          ${openssl_OpenSSL_SSL_SYSTEM_LIBS_%(config)s})
            endif()
            if(DEFINED OpenSSL_LIBRARIES)
                set(OPENSSL_LIBRARIES ${OpenSSL_LIBRARIES})
            endif()
            if(DEFINED OpenSSL_VERSION)
                set(OPENSSL_VERSION ${OpenSSL_VERSION})
                if("${OpenSSL_VERSION}" MATCHES "^([0-9]+)\\.([0-9]+)\\.([0-9]+).*$")
                   set(OPENSSL_VERSION_MAJOR "${CMAKE_MATCH_1}")
                   set(OPENSSL_VERSION_MINOR "${CMAKE_MATCH_2}")
                   set(OPENSSL_VERSION_PATCH "${CMAKE_MATCH_3}")
                   set(OPENSSL_VERSION_COUNT 3)
                endif()
            endif()
            if(DEFINED OpenSSL_VERSION_STRING)
                set(OPENSSL_VERSION_STRING ${OpenSSL_VERSION_STRING})
            endif()
        """% {"config":str(self.settings.build_type).upper()})
        tools.files.save(self, module_file, content)

    @property
    def _module_subfolder(self):
        return os.path.join("lib", "cmake")

    @property
    def _module_file_rel_path(self):
        return os.path.join(self._module_subfolder,
                            f"conan-official-{self.name}-variables.cmake")
                            
    def package_id(self):
        self.info.options.with_unit_tests = "any"

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OpenSSL")
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("pkg_config_name", "openssl")

        self.cpp_info.set_property("cmake_build_modules", [self._module_file_rel_path])
        self.cpp_info.components["ssl"].builddirs.append(self._module_subfolder)
        self.cpp_info.components["ssl"].set_property("cmake_build_modules", [self._module_file_rel_path])
        self.cpp_info.components["crypto"].builddirs.append(self._module_subfolder)
        self.cpp_info.components["crypto"].set_property("cmake_build_modules", [self._module_file_rel_path])

        if self.settings.os == "Windows":
            self.cpp_info.components["ssl"].libs = ["libssl"]
            self.cpp_info.components["crypto"].libs = ["libcrypto"]
        else:
            self.cpp_info.components["ssl"].libs = ["ssl"]
            self.cpp_info.components["crypto"].libs = ["crypto"]

        self.cpp_info.components["ssl"].requires = ["crypto"]

        if self.settings.os == "Windows":
            self.cpp_info.components["crypto"].system_libs.extend(["crypt32", "ws2_32", "advapi32", "user32", "bcrypt"])
        elif self.settings.os == "Linux":
            self.cpp_info.components["crypto"].system_libs.extend(["dl", "rt"])
            self.cpp_info.components["ssl"].system_libs.append("dl")
            self.cpp_info.components["crypto"].system_libs.append("pthread")
            self.cpp_info.components["ssl"].system_libs.append("pthread")

        self.cpp_info.components["crypto"].set_property("cmake_target_name", "OpenSSL::Crypto")
        self.cpp_info.components["crypto"].set_property("pkg_config_name", "libcrypto")
        self.cpp_info.components["crypto"].defines = ["_CRT_SECURE_NO_WARNINGS"]
        
        self.cpp_info.components["ssl"].set_property("cmake_target_name", "OpenSSL::SSL")
        self.cpp_info.components["ssl"].set_property("pkg_config_name", "libssl")
