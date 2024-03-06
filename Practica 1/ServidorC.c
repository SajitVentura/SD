#include <stdio.h>
#include <stdlib.h>
#include <winsock2.h>

int main(int argc, char* argv[]) {
  if (argc != 2) {
    printf("Uso: %s <puerto>\n", argv[0]);
    return 1;
  }

  // Inicializar Winsock
  WSADATA wsa;
  if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
    printf("Error al inicializar Winsock.\n");
    return 1;
  }

  // Crear socket del servidor
  SOCKET serverSocket = socket(AF_INET, SOCK_STREAM, 0);
  if (serverSocket == INVALID_SOCKET) {
    printf("Error al crear el socket del servidor.\n");
    return 1;
  }

  // Configurar la estructura sockaddr_in
  struct sockaddr_in server;
  server.sin_family = AF_INET;
  server.sin_addr.s_addr = INADDR_ANY;
  server.sin_port = htons(atoi(argv[1]));

  // Vincular el socket
  if (bind(serverSocket, (struct sockaddr*)&server, sizeof(server)) == SOCKET_ERROR) {
    printf("Error al vincular el socket.\n");
    closesocket(serverSocket);
    WSACleanup();
    return 1;
  }

  // Escuchar conexiones
  listen(serverSocket, 1);
  printf("Esperando conexiones en el puerto %d...\n", atoi(argv[1]));

  // Aceptar la conexión entrante
  int clientSize = sizeof(struct sockaddr_in);
  SOCKET clientSocket = accept(serverSocket, (struct sockaddr*)&server, &clientSize);
  if (clientSocket == INVALID_SOCKET) {
    printf("Error al aceptar la conexión.\n");
    closesocket(serverSocket);
    WSACleanup();
    return 1;
  }

  printf("Conexión aceptada.\n");

  // Recibir y enviar datos del cliente
  int number;
  do {
    int recvSize = recv(clientSocket, (char*)&number, sizeof(int), 0);
    if (recvSize > 0) {
      // Convertir el número a formato de red
      number = htonl(number);
      // Incrementar el número en 1
      number++;
      // Convertir el número a formato del equipo
      number = ntohl(number);
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

