"""
— ¿Qué hace este programa?
1) Se conecta por TCP a un servidor (HOST, PORT).
2) Lee el saludo inicial del servidor.
3) Pide al usuario su nombre (user) y contraseña (pwd) y envía:  AUTH <user> <pwd>
4) Si el servidor responde con "230 ..." (éxito), inicia un hilo que se queda
    escuchando mensajes del servidor (para no bloquear la consola del usuario).
5) En el hilo receptor, cuando llega un broadcast con el formato
    "250 MSG <user> <texto>", lo imprime como:  [<user>] <texto>
6) En el hilo principal, el usuario puede escribir textos para enviar con
    el comando "MSG <texto>" o salir con "/QUIT" (que manda "QUIT").

— Códigos esperados del servidor (ejemplos):
  * 100 ...  → saludo / info general.
  * 230 ...  → autenticación exitosa.
  * 430 ...  → autenticación fallida.
  * 250 MSG <user> <texto> → broadcast de mensajes.
  * 221 ...  → cierre de sesión/conexión.
  * 403 / 500 → errores varios, según protocolo del servidor.

Función: def recv_loop
Comportamiento
--------------
- Lee una línea a la vez desde el servidor.
- Si la línea empieza con "250 MSG ", la interpreta como un broadcast
    de chat con el formato:  250 MSG <user> <texto>
    y lo imprime como:       [<user>] <texto>
- Para cualquier otro código (100, 230, 430, 221, 403, 500, etc.),
    imprime la línea tal cual para informar al usuario.
- Si recibe un código que empieza con "221 ", asume que el servidor
    está cerrando la sesión y sale del bucle.
- Si readline() devuelve b"" (EOF), significa que el servidor cerró la
    conexión; se informa y se termina el hilo.

Función: def main
Pasos
-----
    1) Crea un socket TCP y se conecta a (HOST, PORT).
    2) Envuelve el socket en un "archivo" binario con makefile("rwb", buffering=0)
        - para facilitar lectura/escritura por líneas (readline / write).
        - buffering=0 → escritura no bufferizada (importante para que los mensajes
        salgan de inmediato cuando hacemos f.write(...)).
    3) Lee el saludo inicial del servidor y lo muestra.
    4) Pide credenciales al usuario y envía:  AUTH <user> <pwd>\n
    5) Lee la respuesta: si NO empieza con "230", aborta (autenticación fallida).
    6) Si autenticó, inicia un hilo (daemon=True) que ejecuta recv_loop(f) para
        escuchar lo que diga el servidor mientras el hilo principal acepta entrada.
    7) En el bucle principal, el usuario puede:
        - Escribir un texto cualquiera → se envía como "MSG <texto>\n".
        - Escribir "/QUIT" (en mayúsculas o minúsculas) → se envía "QUIT\n" y sale.
    8) Si el usuario presiona Ctrl+C (KeyboardInterrupt) o cierra la entrada (EOF),
        se intenta enviar "QUIT\n" para cerrar de forma ordenada.
"""

import socket # Comunicación de red, permite la creación de usuarios y servidores.
import threading # Ejecuta cosas en paralelo, lo que permite "escuchar" al server.
import sys # Acceso.

# Dirección IP del servidor de chat (Laptop BRI).
HOST = "10.136.245.254"
# Puerto TCP del servidor (Revisar puerto libre según el disp).
PORT = 65432


def recv_loop(f):
    try:
        while True:
            line = f.readline()
            if not line:
                print("[Conexión cerrada por el servidor]")
                break

            # Decodifica a str y limpia saltos de línea.
            msg = line.decode("utf-8", errors="replace").strip()

            if msg.startswith("250 MSG "):
                _, _, rest = msg.partition("250 MSG ")
                if " " in rest:
                    user, text = rest.split(" ", 1)
                else:
                    user, text = rest, ""

                # Imprime en formato [usuario] + texto.
                print(f"\r[{user}] {text}")
                print("> ", end="", flush=True)
            else:
                # Cualquier otra línea del servidor se muestra tal cual.
                print(f"\r{msg}")
                # Si el servidor envía 221, se asume cierre ordenado.
                if msg.startswith("221 "):
                    break
                # Vuelve a pintar el prompt para que el usuario siga escribiendo.
                print("> ", end="", flush=True)
    except Exception:
        # Evita que un error en el hilo termine todo el programa.
        pass


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
        # Conexión al servidor
        c.connect((HOST, PORT))

        f = c.makefile("rwb", buffering=0)

        # Lee y muestra el saludo inicial ("100 Bienvenido...")
        print(f.readline().decode("utf-8").strip())

        # Solicita las credenciales al usuario.
        user = input("Usuario: ").strip()
        pwd = input("Password: ").strip()
        f.write(f"AUTH {user} {pwd}\n".encode("utf-8"))

        resp = f.readline().decode("utf-8").strip()
        print(resp)
        if not resp.startswith("230"):
            print("No autenticado. Saliendo.")
            return

        # Lanza el hilo receptor para no bloquear la consola del usuario
        t = threading.Thread(target=recv_loop, args=(f,), daemon=True)
        t.start()

        # Recoge la entrada del usuario y la manda.
        try:
            while True:
                text = input("> ").strip()
                if not text:
                    continue  # Ignora líneas vacías

                # Comando para salir de forma ordenada
                if text.upper() == "/QUIT":
                    f.write(b"QUIT\n")
                    break

                # Envia un mensaje normal de chat
                f.write(f"MSG {text}\n".encode("utf-8"))

        except (KeyboardInterrupt, EOFError):
            # Intenta cerrar sesión si el usuario interrumpe el programa.
            try:
                f.write(b"QUIT\n")
            except Exception:
                pass


if __name__ == "__main__":
    # Ejecuta la función principal (La de arribita).
    main()
