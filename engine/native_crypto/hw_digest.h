#ifndef HW_DIGEST_H
#define HW_DIGEST_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Derives a 32-byte cryptographic hardware identifier digest.
 * Output is written into digest[32]. Returns 0 on success.
 */
int get_hardware_digest(uint8_t digest[32]);

/**
 * Computes a simple integrity checksum over the main module memory image.
 */
uint32_t compute_code_integrity_checksum(void);

#ifdef __cplusplus
}
#endif

#endif /* HW_DIGEST_H */
