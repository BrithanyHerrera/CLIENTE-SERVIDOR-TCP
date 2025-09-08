import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 65432

def recv_loop(f):
    try:
        while True:
            line = f.readline()
            if not line:
                print("[Conexión cerrada por el servidor]")
                break
            msg = line.decode("utf-8", errors="replace").strip()
            # Filtra y muestra broadcasts 250 MSG <user> <text>
            if msg.startswith("250 MSG "):
                _, _, rest = msg.partition("250 MSG ")
                # rest = "<user> <text>"
                if " " in rest:
                    user, text = rest.split(" ", 1)
                else:
                    user, text = rest, ""
                print(f"\r[{user}] {text}")
                print("> ", end="", flush=True)
            else:
                # Otros códigos (100, 230, 430, 221, 403, 500)
                print(f"\r{msg}")
                if msg.startswith("221 "):
                    break
                print("> ", end="", flush=True)
    except Exception:
        pass

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
        c.connect((HOST, PORT))
        f = c.makefile("rwb", buffering=0)

        # Leer saludo
        print(f.readline().decode("utf-8").strip())

        # Autenticación
        user = input("Usuario: ").strip()
        pwd = input("Password: ").strip()
        f.write(f"AUTH {user} {pwd}\n".encode("utf-8"))

        resp = f.readline().decode("utf-8").strip()
        print(resp)
        if not resp.startswith("230"):
            print("No autenticado. Saliendo.")
            return

        # Hilo receptor
        t = threading.Thread(target=recv_loop, args=(f,), daemon=True)
        t.start()

        # Loop de envío
        try:
            while True:
                text = input("> ").strip()
                if not text:
                    continue
                if text.upper() == "/QUIT":
                    f.write(b"QUIT\n")
                    break
                # Enviar como MSG
                f.write(f"MSG {text}\n".encode("utf-8"))
        except (KeyboardInterrupt, EOFError):
            try:
                f.write(b"QUIT\n")
            except:
                pass

if __name__ == "__main__":
    main()
