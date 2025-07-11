// File: my_c_project/src/spi.c

#include "spi.h"
#include <stdbool.h>

static spi_state_t g_spi_state = SPI_STATE_UNINITIALIZED;
static spi_config_t g_spi_config;

static bool is_valid_speed(uint32_t speed) {
    return (speed == 1000000 || speed == 4000000 || speed == 8000000);
}

int spi_init(void) {
    if (g_spi_state != SPI_STATE_UNINITIALIZED) {
        return SPI_ERROR_ALREADY_INITIALIZED;
    }
    g_spi_config.mode = 0;
    g_spi_config.speed_hz = 1000000;
    g_spi_state = SPI_STATE_INITIALIZED;
    return SPI_SUCCESS;
}

int spi_set_config(const spi_config_t* config) {
    if (g_spi_state == SPI_STATE_UNINITIALIZED) {
        return SPI_ERROR_NOT_INITIALIZED;
    }
    if (config == NULL) {
        return SPI_ERROR_NULL_POINTER;
    }
    if (config->mode > 3) {
        return SPI_ERROR_INVALID_ARG;
    }
    if (!is_valid_speed(config->speed_hz)) {
        return SPI_ERROR_INVALID_ARG;
    }
    g_spi_config = *config;
    return SPI_SUCCESS;
}

int spi_transfer(const uint8_t* tx_buffer, uint8_t* rx_buffer, uint16_t len) {
    if (g_spi_state == SPI_STATE_UNINITIALIZED) {
        return SPI_ERROR_NOT_INITIALIZED;
    }
    if (tx_buffer == NULL && rx_buffer == NULL) {
        return SPI_ERROR_INVALID_ARG;
    }
    if (len == 0 || len > 2048) {
        return SPI_ERROR_INVALID_LENGTH;
    }
    g_spi_state = SPI_STATE_BUSY;
    for (uint16_t i = 0; i < len; ++i) {
        uint8_t tx_byte = (tx_buffer) ? tx_buffer[i] : 0xFF;
        uint8_t rx_byte = tx_byte;
        if (rx_buffer) {
            rx_buffer[i] = rx_byte;
        }
    }
    g_spi_state = SPI_STATE_INITIALIZED;
    return SPI_SUCCESS;
}

// --- Test-only helper implementations ---
#ifdef TEST
spi_state_t test_spi_get_state(void) {
    return g_spi_state;
}
spi_config_t test_spi_get_config(void) {
    return g_spi_config;
}
#endif