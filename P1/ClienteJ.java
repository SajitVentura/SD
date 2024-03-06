import java.io.*;
import java.net.*;

public class ClienteJ {
    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Uso: java ClienteJ <IP del servidor> <Puerto>");
            return;
        }

        String serverIP = args[0];
        int port = Integer.parseInt(args[1]);

        try {
            // Establecer conexión con el servidor
            Socket socket = new Socket(serverIP, port);
            System.out.println("Conectado al servidor.");

            // Configurar la entrada y salida de datos
            BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
            DataInputStream in = new DataInputStream(socket.getInputStream());
            DataOutputStream out = new DataOutputStream(socket.getOutputStream());

            int number;

            do {
                // Solicitar al usuario que ingrese un número
                System.out.print("Ingrese un número (o 0 para salir): ");
                number = Integer.parseInt(reader.readLine());

                // Enviar el número al servidor
                out.writeInt(number);
                out.flush();

                // Recibir la respuesta del servidor
                int result = in.readInt();
                System.out.println("Respuesta del servidor: " + result);

            } while (number != 0);

            // Cerrar conexiones
            socket.close();
            in.close();
            out.close();

            System.out.println("Desconectado del servidor. Programa terminado.");

        } catch (IOException e) {
            System.out.println("Error de entrada/salida: " + e.getMessage());
        }
    }
}
