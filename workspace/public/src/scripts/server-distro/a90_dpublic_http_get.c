/*
 * Minimal HTTP GET client for D-public device-local loopback validation.
 */
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

static int parse_port(const char *text) {
    char *end = NULL;
    long port = strtol(text, &end, 10);
    if (text == end || end == NULL || *end != '\0' || port < 1 || port > 65535) {
        return -1;
    }
    return (int)port;
}

int main(int argc, char **argv) {
    const char *host = "127.0.0.1";
    int port = 8080;
    int fd;
    struct sockaddr_in addr;
    const char request[] =
        "GET / HTTP/1.1\r\n"
        "Host: 127.0.0.1\r\n"
        "Connection: close\r\n"
        "\r\n";
    char buffer[512];

    if (argc >= 2) {
        host = argv[1];
    }
    if (argc >= 3) {
        port = parse_port(argv[2]);
        if (port < 0) {
            fprintf(stderr, "bad port\n");
            return 2;
        }
    }

    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("socket");
        return 1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)port);
    if (inet_pton(AF_INET, host, &addr.sin_addr) != 1) {
        fprintf(stderr, "bad host\n");
        close(fd);
        return 2;
    }

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("connect");
        close(fd);
        return 1;
    }

    if (write(fd, request, sizeof(request) - 1) < 0) {
        perror("write");
        close(fd);
        return 1;
    }

    for (;;) {
        ssize_t nread = read(fd, buffer, sizeof(buffer));
        if (nread < 0) {
            if (errno == EINTR) {
                continue;
            }
            perror("read");
            close(fd);
            return 1;
        }
        if (nread == 0) {
            break;
        }
        if (write(STDOUT_FILENO, buffer, (size_t)nread) < 0) {
            perror("stdout");
            close(fd);
            return 1;
        }
    }

    close(fd);
    return 0;
}
