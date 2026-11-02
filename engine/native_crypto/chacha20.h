#ifndef CHACHA20_H
#define CHACHA20_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t state[16];
} chacha20_ctx;

/**
 * Initializes ChaCha20 context with a 256-bit key (32 bytes), 96-bit nonce (12 bytes), and initial counter.
 */
void chacha20_init(chacha20_ctx *ctx, const uint8_t key[32], const uint8_t nonce[12], uint32_t counter);

/**
 * Encrypts/decrypts in-place or from input to output buffer.
 */
void chacha20_xor(chacha20_ctx *ctx, uint8_t *output, const uint8_t *input, size_t length);

/**
 * Ephemeral string decryptor:
 * Decrypts in-place into dest_buffer, calls consumer, and immediately zeroes dest_buffer.
 */
void chacha20_ephemeral_decrypt(const uint8_t *ciphertext, size_t length,
                               const uint8_t key[32], const uint8_t nonce[12],
                               uint8_t *output_buffer);

/**
 * Secure memory zeroization helper (resists dead-store elimination).
 */
void secure_zero_memory(void *v, size_t n);

#ifdef __cplusplus
}
#endif

#endif /* CHACHA20_H */
