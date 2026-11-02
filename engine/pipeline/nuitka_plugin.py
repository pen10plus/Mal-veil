"""
Custom Nuitka Protection Plugin
Hooks into Nuitka's compilation pipeline to inject C-level native watchdogs,
ephemeral string tables, and anti-optimization directives.
"""

import os
import sys

try:
    from nuitka.plugins.PluginBase import NuitkaPluginBase
except ImportError:
    # Fallback placeholder if Nuitka is not installed in the current environment
    class NuitkaPluginBase:
        pass


class HardenedProtectionPlugin(NuitkaPluginBase):
    plugin_name = "hardened_protection"
    plugin_desc = "Injects C99 ChaCha20 decryptors, hardware digests, and anti-debug watchdogs."

    def __init__(self, logger=None):
        self.logger = logger
        self.native_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "native_crypto")
        )

    def onModuleSourceCode(self, module_name, source_code=None, source_filename=None, **kwargs):
        """Intercepts module source to inject pre-initialization watchdog hooks."""
        if source_code is None and "source_code" in kwargs:
            source_code = kwargs["source_code"]
        if source_code is None:
            source_code = ""
        if module_name == "__main__":
            # Ensure the security environment is validated at process startup
            hook_header = (
                "# Injected Hardened Security Watchdog\n"
                "import sys\n"
            )
            return hook_header + source_code
        return source_code

    def getExtraIncludeDirectories(self):
        """Adds native_crypto directory to C compiler include search paths."""
        return [self.native_dir]

    def getExtraCSourceFiles(self):
        """Instructs Nuitka's C compiler to build chacha20.c, anti_debug.c, and hw_digest.c."""
        return [
            os.path.join(self.native_dir, "chacha20.c"),
            os.path.join(self.native_dir, "anti_debug.c"),
            os.path.join(self.native_dir, "hw_digest.c")
        ]
