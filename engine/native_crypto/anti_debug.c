#include "anti_debug.h"
#include <stdlib.h>

#if defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#include <tlhelp32.h>

static int check_windows_debugger(void) {
    int detected = 0;

    /* 1. Standard Win32 API check */
    if (IsDebuggerPresent()) {
        detected |= SECURITY_DETECTED_DEBUGGER;
    }

    /* 2. CheckRemoteDebuggerPresent check */
    BOOL is_remote = FALSE;
    if (CheckRemoteDebuggerPresent(GetCurrentProcess(), &is_remote) && is_remote) {
        detected |= SECURITY_DETECTED_DEBUGGER;
    }

    /* 3. Hardware Breakpoints check (DR0 - DR3 registers) */
    CONTEXT ctx;
    ZeroMemory(&ctx, sizeof(CONTEXT));
    ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
    HANDLE hThread = GetCurrentThread();

    if (GetThreadContext(hThread, &ctx)) {
        if (ctx.Dr0 || ctx.Dr1 || ctx.Dr2 || ctx.Dr3) {
            detected |= SECURITY_DETECTED_HARDWARE_BP;
        }
    }

    /* 4. Detect Frida/DBI modules loaded in memory */
    if (GetModuleHandleA("frida-agent.dll") != NULL ||
        GetModuleHandleA("frida-gadget.dll") != NULL ||
        GetModuleHandleA("hooking.dll") != NULL) {
        detected |= SECURITY_DETECTED_HOOKING_DBI;
    }

    return detected;
}

#elif defined(__linux__)
#include <sys/ptrace.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

static int check_linux_debugger(void) {
    int detected = 0;

    /* 1. ptrace check */
    if (ptrace(PTRACE_TRACEME, 0, 1, 0) < 0) {
        detected |= SECURITY_DETECTED_DEBUGGER;
    } else {
        /* Detach after test */
        ptrace(PTRACE_DETACH, 0, 1, 0);
    }

    /* 2. TracerPid inspection in /proc/self/status */
    FILE *f = fopen("/proc/self/status", "r");
    if (f) {
        char line[128];
        while (fgets(line, sizeof(line), f)) {
            if (strncmp(line, "TracerPid:", 10) == 0) {
                int pid = 0;
                if (sscanf(line + 10, "%d", &pid) == 1 && pid != 0) {
                    detected |= SECURITY_DETECTED_DEBUGGER;
                }
                break;
            }
        }
        fclose(f);
    }

    return detected;
}

#else

static int check_generic_debugger(void) {
    return SECURITY_OK;
}

#endif

int security_check_environment(void) {
#if defined(_WIN32) || defined(_WIN64)
    return check_windows_debugger();
#elif defined(__linux__)
    return check_linux_debugger();
#else
    return check_generic_debugger();
#endif
}

void security_enforce_environment(void) {
    if (security_check_environment() != SECURITY_OK) {
        /* Silent immediate termination */
        exit(1);
    }
}
