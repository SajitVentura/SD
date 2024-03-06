#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>

#define MAX_BUFFER 1024

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Uso: %s <IP del servidor> <puerto>\n", argv[0]);
        exit(1);
    }

    const char *ipServidor = argv[1];
    int puerto = atoi(argv[2]);

    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        fprintf(stderr, "Error al inicializar Winsock\n");
        exit(1);
    }

    int clientSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (clientSocket == INVALID_SOCKET) {
        fprintf(stderr, "Error al crear el socket: %ld\n", WSAGetLastError());
        WSACleanup();
        exit(1);
    }

    struct sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(puerto);
    serverAddr.sin_addr.s_addr = inet_addr(ipServidor);

    if (connect(clientSocket, (struct sockaddr *)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        fprintf(stderr, "Error al conectar con el servidor: %ld\n", WSAGetLastError());
        closesocket(clientSocket);
        WSACleanup();
        exit(1);
    }

    // Enviar mensaje al servidor
    char mensajeCliente[MAX_BUFFER];
    printf("Ingrese un mensaje para el servidor: ");
    fgets(mensajeCliente, MAX_BUFFER, stdin);
    send(clientSocket, mensajeCliente, strlen(mensajeCliente), 0);

    // Recibir respuesta del servidor
    char mensajeServidor[MAX_BUFFER];
    recv(clientSocket, mensajeServidor, MAX_BUFFER, 0);
    printf("Servidor responde: %s\n", mensajeServidor);

    // Cerrar conexión
    closesocket(clientSocket);
    WSACleanup();

    return 0;
}

