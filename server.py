import socket
import threading

HOST = "0.0.0.0"
PORT = 65432

# Usuarios
USERS = {
    "isma": "1234",
    "Ana":"2512",
    "Kevin":"4343",
    "Gibran":"sexoplus",
    "Lalo":"123",
    "Bri":"Bri2"
}

clients = {}  # conn -> {"user": str, "file": filelike}
clients_lock = threading.Lock()

def send_line(f, s: str):
    try:
        f.write((s + "\n").encode("utf-8"))
    except Exception:
        pass

def broadcast(line: str):
    with clients_lock:
        for info in list(clients.values()):
            send_line(info["file"], line)

def handle_client(conn, addr):
    f = conn.makefile("rwb", buffering=0)
    authed = False
    username = None

    send_line(f, "100 READY")

    try:
        while True:
            raw = f.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            # Parseo simple: comando y el resto como payload
            if " " in line:
                cmd, rest = line.split(" ", 1)
            else:
                cmd, rest = line, ""

            cmd = cmd.upper()

            if cmd == "AUTH":
                parts = rest.split(" ", 1)
                if len(parts) != 2:
                    send_line(f, "500 ERROR Missing credentials")
                    continue
                user, pwd = parts[0], parts[1]
                if USERS.get(user) == pwd:
                    authed = True
                    username = user
                    with clients_lock:
                        clients[conn] = {"user": username, "file": f}
                    send_line(f, "230 AUTH OK")
                    # Anuncia ingreso (opcional)
                    broadcast(f"250 MSG server {username} se ha conectado")
                else:
                    send_line(f, "430 AUTH FAIL")

            elif cmd == "MSG":
                if not authed:
                    send_line(f, "403 FORBIDDEN")
                    continue
                # rest es el texto completo, puede tener espacios
                text = rest
                broadcast(f"250 MSG {username} {text}")

            elif cmd == "QUIT":
                send_line(f, "221 BYE")
                break

            else:
                send_line(f, "500 ERROR Unknown command")

    except Exception:
        # Podrías loggear aquí
        pass
    finally:
        # Limpieza
        with clients_lock:
            if conn in clients:
                gone = clients.pop(conn)
                # Aviso de salida (opcional)
                broadcast(f"250 MSG server {gone['user']} salió")
        try:
            f.close()
        except:
            pass
        conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Servidor de chat en {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
