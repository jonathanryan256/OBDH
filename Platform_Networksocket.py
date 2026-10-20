import socket
import time


PF_HOST = '127.0.0.1'
PF_PORT = 5001
PL_PORT = 5002

def run_platform():
    # Telemetry Setup ==================================================================
    # Try to connect to the payload (the payload must already be turned ON)
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

    # Command loop for Platform=============================================================
    current_mode = "SAFE"
    payload_power = "OFF"

    print(f"[PLATFORM] Initial Status: Modus = {current_mode}, Payload = {payload_power}")

    # Run through command loop =============================================================
    while True:
        print(f"\n[PLATFORM] Status: [{current_mode}] | Payload: [{payload_power}] | Waiting for ground...")

        # Reconnect when interrupted =======================================================
        try:
            command = gnd_conn.recv(1024).decode('utf-8').strip()
            if not command:
                print("[PLATFORM] Lost connection with Ground. Waiting for reconnection...")
                gnd_conn, gnd_addr = pf_server.accept() # Wait for new connection to ground.
                continue
        except (ConnectionResetError, ConnectionAbortedError):
            print("[PLATFORM] Connection abruptly cut off! Waiting for reconnection...")
            gnd_conn, gnd_addr = pf_server.accept() # Wait for new connection to ground.
            continue

        # Shut Down system if exit is requested.
        if command.lower() == 'exit':
            print("[PLATFORM] Shutdown signal received, Shutting Down...")
            pl_socket.sendall("exit".encode('utf-8'))
            break

        print(f"[PLATFORM] Received from Ground -> '{command}'")

        # Show MODE ===========================================================================
        if command == "MODE":
            reply = f"PF_TM: STATUS - Current mode is [{current_mode}], (Payload is {payload_power})\n"
            gnd_conn.sendall(reply.encode('utf-8'))


        # Swap-MODE Logic ===================================================================
        elif "SET-MODE" in command:
            new_mode = command.replace("SET-MODE ", "").upper()

            if new_mode in ["SAFE", "TARGET"]:
                # Check if this is not the current mode
                if new_mode == current_mode:
                    reply = f"PF_TM: REJECT - Mode switch rejected. Satellite is already in {current_mode} mode!\n"
                    gnd_conn.sendall(reply.encode('utf-8'))
                    print(f"[PLATFORM] Mode switch ignored: {current_mode} is already active.")
                else:
                    init_reply = f"PF_TM: INIT - Mode switch to {new_mode} initialized...\n"
                    gnd_conn.sendall(init_reply.encode('utf-8'))
                    print(f"[PLATFORM] Mode switch to {new_mode} initialized... (Duration of 3 seconds)")
                    
                    time.sleep(3)

                    current_mode = new_mode

                    # Automatic shutdown of payload while switching to SAFE
                    if current_mode == "SAFE" and payload_power == "ON":
                        payload_power = "OFF"
                        print(f"[PLATFORM] EVENT: Satellite switched to SAFE! -> Automatic shutdown of Payload.")
                        pl_socket.sendall("SET-POWER OFF".encode('utf-8'))
                        try: pl_socket.recv(1024) # Ignore response
                        except: pass

                    reply = f"PF_TM: EVENT - Mode succesfully switched to {current_mode}\n"
                    gnd_conn.sendall(reply.encode('utf-8'))
                    continue
            else:
                reply = f"PF_TM: REJECT - Unknown mode '{new_mode}'\n"
                gnd_conn.sendall(reply.encode('utf-8'))

            continue
            

        # Commands for PAYLOAD ================================================================
        elif "PAYLOAD" in command:
            # Reject any command when SAFE-MODE is active.
            if current_mode == "SAFE":
                reply = "PF_TM: REJECT - Payload command rejected. Current mode = SAFE\n"
                gnd_conn.sendall(reply.encode('utf-8'))
                continue

            # When mode is not SAFE we continue with the payload commands.
            if "POWER-ON" in command:
                payload_power = "ON"
            elif "POWER-OFF" in command:
                payload_power = "OFF"

            # Forward command to payload.
            print("[PLATFORM] Forwarding command to Payload...")
            pl_socket.sendall(command.encode('utf-8'))

            while True:
                pl_reply = pl_socket.recv(1024).decode('utf-8').strip()
                if not pl_reply:
                    break

                gnd_conn.sendall(f"PF_TM: Forwarding -> {pl_reply}\n".encode('utf-8'))
                print(f"[PLATFORM] Forwarded to ground: {pl_reply}")

                if "EVENT" in pl_reply:
                    break
                elif "INIT" in pl_reply:
                    continue
                else:
                    break
            continue

    # Shut down server ======================================================================
    print("[PLATFORM] Server shutting down...")
    gnd_conn.close()
    pf_server.close()
    pl_socket.close()

if __name__ == "__main__":
    run_platform()

