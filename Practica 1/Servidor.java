import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;

public class Servidor {
    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Uso: java Servidor <puerto>");
            System.exit(1);
        }

        int puerto = Integer.parseInt(args[0]);

        try {
            ServerSocket serverSocket = new ServerSocket(puerto);
            System.out.println("Servidor esperando conexiones en el puerto " + puerto);

            Socket clientSocket = serverSocket.accept();
            System.out.println("Cliente conectado desde " + clientSocket.getInetAddress());

            BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
            PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);

            String mensajeCliente = in.readLine();
            System.out.println("Cliente dice: " + mensajeCliente);

            // Responder al cliente
            out.println("Hola que tal");

            // Cerrar conexiones
            in.close();
            out.close();
            clientSocket.close();
            serverSocket.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
