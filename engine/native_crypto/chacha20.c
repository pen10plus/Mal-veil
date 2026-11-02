#include "chacha20.h"
#include <string.h>

#define ROTL32(v, n) (((v) << (n)) | ((v) >> (32 - (n))))

#define CHACHA20_QUARTERROUND(a, b, c, d) \
    do { \
        a += b; d ^= a; d = ROTL32(d, 16); \
        c += d; b ^= c; b = ROTL32(b, 12); \
        a += b; d ^= a; d = ROTL32(d, 8);  \
        c += d; b ^= c; b = ROTL32(b, 7);  \
    } while (0)

static uint32_t load32_le(const uint8_t *p) {
    return (uint32_t)p[0] |
           ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) |
           ((uint32_t)p[3] << 24);
}

static void store32_le(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v);
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}

void secure_zero_memory(void *v, size_t n) {
    volatile uint8_t *p = (volatile uint8_t *)v;
    while (n--) {
        *p++ = 0;
    }
}

void chacha20_init(chacha20_ctx *ctx, const uint8_t key[32], const uint8_t nonce[12], uint32_t counter) {
    /* Constants "expand 32-byte k" */
    ctx->state[0] = 0x61707865;
    ctx->state[1] = 0x3320646e;
    ctx->state[2] = 0x79622d32;
    ctx->state[3] = 0x6b206574;

    /* Key */
    ctx->state[4]  = load32_le(key + 0);
    ctx->state[5]  = load32_le(key + 4);
    ctx->state[6]  = load32_le(key + 8);
    ctx->state[7]  = load32_le(key + 12);
    ctx->state[8]  = load32_le(key + 16);
    ctx->state[9]  = load32_le(key + 20);
    ctx->state[10] = load32_le(key + 24);
    ctx->state[11] = load32_le(key + 28);

    /* Block Counter */
    ctx->state[12] = counter;

    /* Nonce */
    ctx->state[13] = load32_le(nonce + 0);
    ctx->state[14] = load32_le(nonce + 4);
    ctx->state[15] = load32_le(nonce + 8);
}

static void chacha20_block(chacha20_ctx *ctx, uint8_t output[64]) {
    uint32_t x[16];
    int i;

    for (i = 0; i < 16; i++) {
        x[i] = ctx->state[i];
    }

    /* 10 double rounds = 20 rounds */
    for (i = 0; i < 10; i++) {
        /* Column round */
        CHACHA20_QUARTERROUND(x[0], x[4], x[8],  x[12]);
        CHACHA20_QUARTERROUND(x[1], x[5], x[9],  x[13]);
        CHACHA20_QUARTERROUND(x[2], x[6], x[10], x[14]);
        CHACHA20_QUARTERROUND(x[3], x[7], x[11], x[15]);

        /* Diagonal round */
        CHACHA20_QUARTERROUND(x[0], x[5], x[10], x[15]);
        CHACHA20_QUARTERROUND(x[1], x[6], x[11], x[12]);
        CHACHA20_QUARTERROUND(x[2], x[7], x[8],  x[13]);
        CHACHA20_QUARTERROUND(x[3], x[4], x[9],  x[14]);
    }

    for (i = 0; i < 16; i++) {
        x[i] += ctx->state[i];
        store32_le(output + (i * 4), x[i]);
    }

    /* Increment block counter */
    ctx->state[12]++;
}

void chacha20_xor(chacha20_ctx *ctx, uint8_t *output, const uint8_t *input, size_t length) {
    uint8_t keystream[64];
    size_t i, chunk;

    while (length > 0) {
        chacha20_block(ctx, keystream);
        chunk = (length < 64) ? length : 64;

        for (i = 0; i < chunk; i++) {
            output[i] = input[i] ^ keystream[i];
        }

        output += chunk;
        input += chunk;
        length -= chunk;
    }

    secure_zero_memory(keystream, sizeof(keystream));
}

void chacha20_ephemeral_decrypt(const uint8_t *ciphertext, size_t length,
                               const uint8_t key[32], const uint8_t nonce[12],
                               uint8_t *output_buffer) {
    chacha20_ctx ctx;
    chacha20_init(&ctx, key, nonce, 1);
    chacha20_xor(&ctx, output_buffer, ciphertext, length);
    secure_zero_memory(&ctx, sizeof(ctx));
}
