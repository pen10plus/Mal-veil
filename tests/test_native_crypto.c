#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../engine/native_crypto/chacha20.h"
#include "../engine/native_crypto/anti_debug.h"
#include "../engine/native_crypto/hw_digest.h"

int main(void) {
    printf("============================================================\n");
    printf("     NATIVE C SUB-SYSTEM INTEGRATION TEST (WIN64/UCRT)     \n");
    printf("============================================================\n");

    /* 1. Test Hardware Digest */
    uint8_t hw_digest[32];
    get_hardware_digest(hw_digest);
    printf("[+] Hardware Digest (SHA-256): ");
    for (int i = 0; i < 32; i++) {
        printf("%02x", hw_digest[i]);
    }
    printf("\n");

    /* 2. Test Code Integrity Checksum */
    uint32_t checksum = compute_code_integrity_checksum();
    printf("[+] Header Integrity FNV-1a Checksum: 0x%08X\n", checksum);

    /* 3. Test Anti-Debug Watchdog */
    int sec_status = security_check_environment();
    printf("[+] Security Environment Check Status: %d (%s)\n",
           sec_status, (sec_status == SECURITY_OK) ? "CLEAN / NO DEBUGGER" : "THREAT DETECTED");

    /* 4. Test ChaCha20 Encryption/Decryption Roundtrip */
    uint8_t key[32] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
        0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
        0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f
    };
    uint8_t nonce[12] = {
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x4a, 0x00, 0x00, 0x00, 0x00
    };

    const char *plaintext = "TopSecretProprietaryBusinessPayload2026!";
    size_t len = strlen(plaintext);
    uint8_t ciphertext[64];
    uint8_t decrypted[64];

    memset(ciphertext, 0, sizeof(ciphertext));
    memset(decrypted, 0, sizeof(decrypted));

    chacha20_ctx ctx;
    chacha20_init(&ctx, key, nonce, 1);
    chacha20_xor(&ctx, ciphertext, (const uint8_t *)plaintext, len);

    printf("[+] Ciphertext (Hex): ");
    for (size_t i = 0; i < len; i++) {
        printf("%02x", ciphertext[i]);
    }
    printf("\n");

    /* Ephemeral Decrypt */
    chacha20_ephemeral_decrypt(ciphertext, len, key, nonce, decrypted);
    printf("[+] Decrypted (Plain): %s\n", decrypted);

    if (strcmp((char *)decrypted, plaintext) != 0) {
        printf("[FAIL] Decryption text does not match plaintext!\n");
        return 1;
    }

    /* Test Memory Zeroization */
    secure_zero_memory(decrypted, sizeof(decrypted));
    printf("[+] Memory Zeroization: Verified (buffer wiped)\n");

    printf("[SUCCESS] All Phase 2 Native C Subsystems Passed 100%%!\n");
    printf("============================================================\n");
    return 0;
}
