#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "s22plus_o3_freestanding_protocol.h"

static size_t build_request(uint8_t *output, uint32_t sequence, const uint8_t *payload, size_t length) {
    size_t index;
    for (index = 0; index < 4U; ++index) {
        output[index] = (uint8_t)S22PLUS_O3F_MAGIC[index];
    }
    output[4] = S22PLUS_O3F_VERSION;
    output[5] = S22PLUS_O3F_REQUEST;
    s22plus_o3f_store_le16(&output[6], (uint16_t)length);
    s22plus_o3f_store_le32(&output[8], sequence);
    s22plus_o3f_store_le32(&output[12], 0U);
    memcpy(&output[S22PLUS_O3F_HEADER_SIZE], payload, length);
    s22plus_o3f_store_le32(
        &output[12],
        s22plus_o3f_frame_crc(output, &output[S22PLUS_O3F_HEADER_SIZE], length)
    );
    return S22PLUS_O3F_HEADER_SIZE + length;
}

static int check_payload(const uint8_t *payload, size_t length, uint32_t sequence) {
    uint8_t frame[S22PLUS_O3F_MAX_FRAME];
    uint8_t response[S22PLUS_O3F_MAX_FRAME];
    struct s22plus_o3f_request_view view;
    size_t frame_size = build_request(frame, sequence, payload, length);
    size_t response_size;
    if (s22plus_o3f_validate_request(frame, frame_size, &view) != S22PLUS_O3F_FRAME_OK) {
        return 1;
    }
    if (view.sequence != sequence || view.payload_length != length ||
        memcmp(view.payload, payload, length) != 0) {
        return 2;
    }
    response_size = s22plus_o3f_build_response(
        response,
        sizeof(response),
        sequence,
        payload,
        length
    );
    if (response_size != frame_size || response[5] != S22PLUS_O3F_RESPONSE ||
        s22plus_o3f_load_le32(&response[8]) != sequence ||
        s22plus_o3f_frame_crc(response, &response[S22PLUS_O3F_HEADER_SIZE], length) !=
            s22plus_o3f_load_le32(&response[12])) {
        return 3;
    }
    return 0;
}

int main(void) {
    uint8_t payload[S22PLUS_O3F_MAX_PAYLOAD];
    uint8_t frame[S22PLUS_O3F_MAX_FRAME];
    struct s22plus_o3f_request_view view;
    size_t index;
    size_t frame_size;
    for (index = 0; index < sizeof(payload); ++index) {
        payload[index] = (uint8_t)(index * 17U + 3U);
    }
    if (check_payload(payload, 0, 0U) != 0 ||
        check_payload(payload, 31, UINT32_C(0x12345678)) != 0 ||
        check_payload(payload, sizeof(payload), UINT32_MAX) != 0) {
        return 1;
    }
    frame_size = build_request(frame, 7U, payload, 32U);
    frame[frame_size - 1U] ^= 0x80U;
    if (s22plus_o3f_validate_request(frame, frame_size, &view) != S22PLUS_O3F_FRAME_CRC) {
        return 2;
    }
    frame_size = build_request(frame, 8U, payload, 8U);
    frame[5] = S22PLUS_O3F_RESPONSE;
    if (s22plus_o3f_validate_request(frame, frame_size, &view) != S22PLUS_O3F_FRAME_TYPE) {
        return 3;
    }
    frame_size = build_request(frame, 9U, payload, 8U);
    if (s22plus_o3f_validate_request(frame, frame_size - 1U, &view) != S22PLUS_O3F_FRAME_LENGTH) {
        return 4;
    }
    if (s22plus_o3f_validate_request(frame, 8U, &view) != S22PLUS_O3F_FRAME_SHORT) {
        return 5;
    }
    if (s22plus_o3f_build_response(frame, sizeof(frame), 1U, payload, sizeof(payload) + 1U) != 0) {
        return 6;
    }
    puts("s22plus_o3_freestanding_protocol_test=PASS");
    return 0;
}
