## `spi_init`

### Description
Initializes the SPI peripheral. This function must be called before any other SPI function.

### Functional Requirements
- The function must configure the SPI peripheral for Master Mode.
- It must set the clock polarity and phase to Mode 0 (CPOL=0, CPHA=0).
- The default clock speed must be set to 1 MHz.
- On successful initialization, the internal driver state must be set to `SPI_STATE_INITIALIZED`.

### Error Handling
- If the SPI hardware is already initialized, the function must return `SPI_ERROR_ALREADY_INITIALIZED` without re-configuring the hardware.

---

## `spi_set_config`

### Description
Configures the SPI clock speed and mode. Can only be called after `spi_init`.

### Parameters
- `config`: A pointer to an `spi_config_t` struct containing the desired configuration.

### Functional Requirements
- Must correctly apply the `speed_hz` and `mode` from the config struct to the hardware registers.
- The `mode` parameter must be a value between 0 and 3, inclusive.
- The `speed_hz` must be one of the following allowed values: 1000000 (1MHz), 4000000 (4MHz), 8000000 (8MHz).

### Error Handling
- If the driver has not been initialized via `spi_init`, the function must return `SPI_ERROR_NOT_INITIALIZED`.
- If the `config` pointer is `NULL`, it must return `SPI_ERROR_NULL_POINTER`.
- If an unsupported `mode` is provided, it must return `SPI_ERROR_INVALID_ARG`.
- If an unsupported `speed_hz` is provided, it must return `SPI_ERROR_INVALID_ARG`.

---

## `spi_transfer`

### Description
Transmits a block of data and simultaneously receives a block of data.

### Parameters
- `tx_buffer`: A pointer to the data buffer to transmit. Can be `NULL` if only receiving data.
- `rx_buffer`: A pointer to the buffer where received data will be stored. Can be `NULL` if only transmitting.
- `len`: The number of bytes to transfer.

### Functional Requirements
- The function must perform a bidirectional transfer of `len` bytes.
- If `tx_buffer` is `NULL`, the driver must transmit `0xFF` for the duration of the transfer.
- If `rx_buffer` is `NULL`, received data must be discarded.
- The maximum transfer length is 2048 bytes.

### Error Handling
- If the driver has not been initialized, it must return `SPI_ERROR_NOT_INITIALIZED`.
- If both `tx_buffer` and `rx_buffer` are `NULL`, it must return `SPI_ERROR_INVALID_ARG`.
- If `len` is 0 or greater than 2048, it must return `SPI_ERROR_INVALID_LENGTH`.