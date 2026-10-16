import socket


PL_HOST = '127.0.0.1'
PL_PORT = 5002

def run_payload():
    # Start the server for the platform to connect to.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((PL_HOST, PL_PORT))
    server.listen(1)
    print(f"[PAYLOAD] Started, listening on port {PL_PORT}...")

    conn, addr = server.accept()
    print(f"[PAYLOAD] Connected to Platform OBC via {addr}")

    while True:
        command = conn.recv(1024).decode('utf-8')
        if not command or command.lower() == 'exit':
            print("[PAYLOAD] Connection lost.")
            break

        print(f"[PAYLOAD] Command received from Platform: {command}")

        # Processing data
        if "TAKE-IMAGE" in command:
            reply = "PL_TM: IMAGE_START"
        else:
            reply = f"PL_TM: ACK {command}"

        conn.send(reply.encode('utf-8'))

    conn.close()
    server.close()

if __name__ == "__main__":
    run_payload()