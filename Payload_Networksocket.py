import socket
import time
from datetime import datetime


PL_HOST = '127.0.0.1'
PL_PORT = 5002

def run_payload():
    # Telemetry Setup ======================================================================
    # Start the server for the platform to connect to.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((PL_HOST, PL_PORT))
    server.listen(1)
    print(f"[PAYLOAD] Started, listening on port {PL_PORT}...")

    conn, addr = server.accept()
    print(f"[PAYLOAD] Connected to Platform OBC via {addr}.")
    
    # Command loop for Payload =============================================================
    payload_status = "OFF"
    print(f"[PAYLOAD] Initial status: {payload_status}")

    while True:
        command = conn.recv(1024).decode('utf-8').strip()
        if not command or command.lower() == "exit":
            print("[PAYLOAD] Connection lost.")
            break

        print(f"[PAYLOAD] Command received: '{command}'")

        # Command to power ON the payload.
        if "POWER-ON" in command:
            payload_status = "ON"
            reply = "PL_TM: STATUS - Payload is now POWERED-ON\n"
            print("[PAYLOAD] Status modified to POWERED-ON.")

        # Command to power OFF the payload.
        elif "POWER-OFF" in command:
            payload_status = "OFF"
            reply = "PL_TM: STATUS - Payload is now POWERED-OFF\n"
            print("[PAYLOAD] Status modified to POWERED-OFF.")

        # Command to take the IMAGE.
        elif "TAKE-IMAGE" in command:
            if payload_status == "OFF":
                reply = "PL_TM: REJECT - Cannot take image. Payload is POWERED-OFF!\n"
                print("[PAYLOAD] FAILURE: Image rejected, Payload is powered off.")
            else:
                reply = "PL_TM: INIT - Image capture initialized...\n"
                print("[PAYLOAD] Image capture accepted...")
                conn.sendall(reply.encode('utf-8'))

                time.sleep(5)

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                with open("Image_Log.txt", "a") as logfile:
                    logfile.write(f"[{now}] Image successfully captured and stored in Mass Memory Unit.\n")

                print("[PAYLOAD] Image successfully captured and saved in Image_Log.txt!")

                time.sleep(0.1)
                
                reply = "PL_TM: EVENT - Image capture FINISHED, data logged successfully (duration is 5 seconds)\n"
                conn.sendall(reply.encode("utf-8"))
                continue

        # Automatic POWER OFF while switching to SAFE mode.
        elif "SET-POWER OFF" in command:
            payload_status = "OFF"
            reply = "PL_TM: STATUS - Emergency shutdown completed due to active SAFE mode\n"
            print("[PAYLOAD] Emergency stop received! Status is OFF!")

        # When command is unknown.
        else:
            reply = f"PL_TM: REJECT - Unknown Payload command '{command}'\n"

        conn.sendall(reply.encode('utf-8'))


    conn.close()
    server.close()



if __name__ == "__main__":
    run_payload()