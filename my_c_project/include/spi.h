#ifndef SPI_H
#define SPI_H

#include <stdint.h>
#include <stddef.h>

// Error codes
#define SPI_SUCCESS 0
#define SPI_ERROR_NULL_POINTER -1
#define SPI_ERROR_INVALID_LENGTH -2

int spi_write(uint8_t* data, uint16_t len);

#endif // SPI_H
