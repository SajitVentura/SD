#include <stdio.h>
#include <stdlib.h>
#include <winsock2.h>

int main() {
    WSADATA wsa;
    SOCKET serverSocket, clientSocket;
    struct sockaddr_in server, client;
    int recvSize, number, port;

    // Inicializar Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        printf("Error al inicializar Winsock.\n");
        return 1;
    }

    // Solicitar al usuario que ingrese el puerto
    printf("Ingrese el puerto para escuchar: ");
    scanf("%d", &port);

    // Crear socket del servidor
    if ((serverSocket = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCKET) {
        printf("Error al crear el socket del servidor.\n");
        return 1;
    }

    // Configurar la estructura sockaddr_in
    server.sin_family = AF_INET;
    server.sin_addr.s_addr = INADDR_ANY;
    server.sin_port = htons(port);

    // Vincular el socket
    if (bind(serverSocket, (struct sockaddr*)&server, sizeof(server)) == SOCKET_ERROR) {
        printf("Error al vincular el socket.\n");
        closesocket(serverSocket);
        WSACleanup();
        return 1;
    }

    // Escuchar conexiones
    listen(serverSocket, 1);
    printf("Esperando conexiones en el puerto %d...\n", port);

    // Aceptar la conexión entrante
    int clientSize = sizeof(struct sockaddr_in);
    clientSocket = accept(serverSocket, (struct sockaddr*)&client, &clientSize);
    if (clientSocket == INVALID_SOCKET) {
        printf("Error al aceptar la conexión.\n");
        closesocket(serverSocket);
        WSACleanup();
        return 1;
    }

    printf("Conexión aceptada.\n");

    // Recibir y enviar datos del cliente
    do {
        recvSize = recv(clientSocket, (char*)&number, sizeof(int), 0);
        if (recvSize > 0) {
            // Incrementar el número en 1
            number++;
            // Enviar el número incrementado
            send(clientSocket, (char*)&number, sizeof(int), 0);
        }
    } while (number != 0);

    // Cerrar sockets y limpiar Winsock
    closesocket(clientSocket);
    closesocket(serverSocket);
    WSACleanup();

    printf("Conexión cerrada. Programa terminado.\n");

    return 0;
}

