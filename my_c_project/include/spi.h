// File: my_c_project/include/spi.h

#ifndef SPI_H
#define SPI_H

#include <stdint.h>
#include <stddef.h>

// --- Error Codes ---
#define SPI_SUCCESS                 0
#define SPI_ERROR_NULL_POINTER      -1
#define SPI_ERROR_INVALID_LENGTH    -2
#define SPI_ERROR_NOT_INITIALIZED   -3
#define SPI_ERROR_ALREADY_INITIALIZED -4
#define SPI_ERROR_INVALID_ARG       -5

// --- Driver States ---
typedef enum {
    SPI_STATE_UNINITIALIZED,
    SPI_STATE_INITIALIZED,
    SPI_STATE_BUSY
} spi_state_t;

// --- Configuration Struct ---
typedef struct {
    uint32_t speed_hz; // Clock speed in Hz
    uint8_t  mode;     // SPI Mode (0, 1, 2, or 3)
} spi_config_t;

int spi_init(void);
int spi_set_config(const spi_config_t* config);
int spi_transfer(const uint8_t* tx_buffer, uint8_t* rx_buffer, uint16_t len);

// --- Test-only helper functions for observing internal state ---
#ifdef TEST
spi_state_t test_spi_get_state(void);
spi_config_t test_spi_get_config(void);
#endif

#endif // SPI_H