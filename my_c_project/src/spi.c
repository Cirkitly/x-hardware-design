#include "spi.h" // Use the new header

/**
 * @brief Writes a block of data to the SPI bus.
 * 
 * @param data Pointer to the data buffer.
 * @param len The number of bytes to write. Must be > 0.
 * @return int 0 on success, error code otherwise.
 */
int spi_write(uint8_t* data, uint16_t len) {
    if (data == NULL) {
        return SPI_ERROR_NULL_POINTER;
    }

    if (len == 0) {
        return SPI_ERROR_INVALID_LENGTH;
    }
    
    // Platform-specific SPI write logic would go here.
    return SPI_SUCCESS;
}
