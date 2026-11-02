#ifndef ANTI_DEBUG_H
#define ANTI_DEBUG_H

#ifdef __cplusplus
extern "C" {
#endif

#define SECURITY_OK                     0
#define SECURITY_DETECTED_DEBUGGER      (1 << 0)
#define SECURITY_DETECTED_HARDWARE_BP   (1 << 1)
#define SECURITY_DETECTED_HOOKING_DBI   (1 << 2)

/**
 * Checks system environment for active debuggers, hardware breakpoints, and DBI hooks.
 * Returns SECURITY_OK (0) if clean, or a bitmask of detected threats.
 */
int security_check_environment(void);

/**
 * Active watchdog enforcement:
 * Executes security check; if threats are detected, terminates immediately.
 */
void security_enforce_environment(void);

#ifdef __cplusplus
}
#endif

#endif /* ANTI_DEBUG_H */
