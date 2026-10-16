import socket
import time

PF_HOST = '127.0.0.1'
PF_PORT = 5001
PL_PORT = 5002

def run_platform():
    # Try to connect to the payload (the payload must already be turned ON).
    print("[PLATFORM] Connecting to Payload...")
    pl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try: 
            pl_socket.connect((PF_HOST, PL_PORT))
            print("[PLATFORM] Successfully connected to Payload.")
            break
        except ConnectionRefusedError:
            print("[PLATFORM] Non-active, wait 2 seconds...")
            time.sleep(2)

    # Start the server for the ground station.
    pf_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pf_server.bind((PF_HOST, PF_PORT))
    pf_server.listen(1)
    print(f"[PLATFORM] Listening to Ground on port {PF_PORT}...")

    gnd_conn, gnd_addr = pf_server.accept()
    print(f"[PLATFORM] Connected to Ground MCS via {gnd_addr}")

    while True:
        # Receive commands from ground
        command = gnd_conn.recv(1024).decode('utf-8')
        if not command or command.lower() == 'exit':
            print("[PLATFORM] Connection to Ground closed.")
            # Close the payload connection
            pl_socket.send("exit".encode('utf-8'))
            break

    print(f"[PLATFORM] Reveived from Ground: '{command}'")

    # Send Payload commands directly to Payload.
    if "PAYLOAD" in command or "IMAGE" in command:
        print(f"[PLATFORM] Send commando to Payload...")
        pl_socket.send(command.encode('utf-8'))

        # Wait for an answer from Payload.
        pl_reply = pl_socket.recv(1024).decode('utf-8')
        print(f"[PLATFORM] Telemetry received from Payload: {pl_reply}")

        # Send telemetry to Ground
        gnd_conn.send(f"PF_TM: Forwarding -> {pl_reply}".encode('utf-8'))
    else:
        # Platform sends command itself (mode-switch).
        reply = f"PF_TM: ACK - Platform processed {command}"
        gnd_conn.send(reply.encode('utf-8'))

    gnd_conn.close()
    pf_server.close()
    pl_socket.close()

if __name__ == "__main__":
    run_platform()

