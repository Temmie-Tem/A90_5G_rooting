#ifndef S22PLUS_O3_FREESTANDING_PROTOCOL_H
#define S22PLUS_O3_FREESTANDING_PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#define S22PLUS_O3F_MAGIC "S2O0"
#define S22PLUS_O3F_VERSION 1U
#define S22PLUS_O3F_REQUEST 1U
#define S22PLUS_O3F_RESPONSE 2U
#define S22PLUS_O3F_HEADER_SIZE 16U
#define S22PLUS_O3F_MAX_PAYLOAD 1024U
#define S22PLUS_O3F_MAX_FRAME (S22PLUS_O3F_HEADER_SIZE + S22PLUS_O3F_MAX_PAYLOAD)

enum s22plus_o3f_frame_status {
    S22PLUS_O3F_FRAME_OK = 0,
    S22PLUS_O3F_FRAME_SHORT = -1,
    S22PLUS_O3F_FRAME_MAGIC = -2,
    S22PLUS_O3F_FRAME_TYPE = -3,
    S22PLUS_O3F_FRAME_LENGTH = -4,
    S22PLUS_O3F_FRAME_CRC = -5,
};

struct s22plus_o3f_request_view {
    uint32_t sequence;
    uint16_t payload_length;
    const uint8_t *payload;
};

static inline uint16_t s22plus_o3f_load_le16(const uint8_t *input) {
    return (uint16_t)input[0] | ((uint16_t)input[1] << 8);
}

static inline uint32_t s22plus_o3f_load_le32(const uint8_t *input) {
    return (uint32_t)input[0] |
           ((uint32_t)input[1] << 8) |
           ((uint32_t)input[2] << 16) |
           ((uint32_t)input[3] << 24);
}

static inline void s22plus_o3f_store_le16(uint8_t *output, uint16_t value) {
    output[0] = (uint8_t)value;
    output[1] = (uint8_t)(value >> 8);
}

static inline void s22plus_o3f_store_le32(uint8_t *output, uint32_t value) {
    output[0] = (uint8_t)value;
    output[1] = (uint8_t)(value >> 8);
    output[2] = (uint8_t)(value >> 16);
    output[3] = (uint8_t)(value >> 24);
}

static inline uint32_t s22plus_o3f_crc32_update(uint32_t crc, const uint8_t *data, size_t length) {
    size_t index;
    crc = ~crc;
    for (index = 0; index < length; ++index) {
        unsigned int bit;
        crc ^= data[index];
        for (bit = 0; bit < 8U; ++bit) {
            uint32_t mask = (uint32_t)-(int32_t)(crc & 1U);
            crc = (crc >> 1) ^ (UINT32_C(0xedb88320) & mask);
        }
    }
    return ~crc;
}

static inline uint32_t s22plus_o3f_frame_crc(
    const uint8_t header[S22PLUS_O3F_HEADER_SIZE],
    const uint8_t *payload,
    size_t payload_length
) {
    uint32_t crc = s22plus_o3f_crc32_update(0U, header, 12U);
    return s22plus_o3f_crc32_update(crc, payload, payload_length);
}

static inline int s22plus_o3f_validate_request(
    const uint8_t *frame,
    size_t frame_length,
    struct s22plus_o3f_request_view *view
) {
    uint16_t payload_length;
    uint32_t received_crc;
    size_t index;
    if (frame == NULL || view == NULL || frame_length < S22PLUS_O3F_HEADER_SIZE) {
        return S22PLUS_O3F_FRAME_SHORT;
    }
    for (index = 0; index < 4U; ++index) {
        if (frame[index] != (uint8_t)S22PLUS_O3F_MAGIC[index]) {
            return S22PLUS_O3F_FRAME_MAGIC;
        }
    }
    if (frame[4] != S22PLUS_O3F_VERSION || frame[5] != S22PLUS_O3F_REQUEST) {
        return S22PLUS_O3F_FRAME_TYPE;
    }
    payload_length = s22plus_o3f_load_le16(&frame[6]);
    if (payload_length > S22PLUS_O3F_MAX_PAYLOAD ||
        frame_length != S22PLUS_O3F_HEADER_SIZE + (size_t)payload_length) {
        return S22PLUS_O3F_FRAME_LENGTH;
    }
    received_crc = s22plus_o3f_load_le32(&frame[12]);
    if (s22plus_o3f_frame_crc(frame, &frame[S22PLUS_O3F_HEADER_SIZE], payload_length) != received_crc) {
        return S22PLUS_O3F_FRAME_CRC;
    }
    view->sequence = s22plus_o3f_load_le32(&frame[8]);
    view->payload_length = payload_length;
    view->payload = &frame[S22PLUS_O3F_HEADER_SIZE];
    return S22PLUS_O3F_FRAME_OK;
}

static inline size_t s22plus_o3f_build_response(
    uint8_t *output,
    size_t output_capacity,
    uint32_t sequence,
    const uint8_t *payload,
    size_t payload_length
) {
    size_t index;
    size_t total = S22PLUS_O3F_HEADER_SIZE + payload_length;
    if (output == NULL || payload == NULL || payload_length > S22PLUS_O3F_MAX_PAYLOAD ||
        output_capacity < total) {
        return 0;
    }
    for (index = 0; index < 4U; ++index) {
        output[index] = (uint8_t)S22PLUS_O3F_MAGIC[index];
    }
    output[4] = S22PLUS_O3F_VERSION;
    output[5] = S22PLUS_O3F_RESPONSE;
    s22plus_o3f_store_le16(&output[6], (uint16_t)payload_length);
    s22plus_o3f_store_le32(&output[8], sequence);
    s22plus_o3f_store_le32(&output[12], 0U);
    for (index = 0; index < payload_length; ++index) {
        output[S22PLUS_O3F_HEADER_SIZE + index] = payload[index];
    }
    s22plus_o3f_store_le32(
        &output[12],
        s22plus_o3f_frame_crc(output, &output[S22PLUS_O3F_HEADER_SIZE], payload_length)
    );
    return total;
}

#endif
