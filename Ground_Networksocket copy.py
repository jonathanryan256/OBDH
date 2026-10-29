import socket
import threading
from datetime import datetime

PF_HOST = '127.0.0.1'
PF_PORT = 5001

# CREATE the BACKGROUND Thread ============================================================
def recv_TM_thread(gnd_socket):
    buffer = ""

    try:
        while True:
            # Listen constantly to incoming data
            data = gnd_socket.recv(1024).decode('utf-8')
            if not data:
                print("\n[GROUND] Lost connection to ground...")
                break

            buffer += data

            # Process all complete received lines of data separated by \n
            if "\n" in buffer:
                lines = buffer.split("\n")
                clean_line = lines[0].strip() # Take first line
                buffer = "\n".join(lines[1:]) # Save the rest into the buffer

                buffer = lines.pop() # Save residu

                if clean_line:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    with open("HouseKeeping_log.txt", "a") as logfile:
                        logfile.write(f"[{timestamp}] RECEIVED TM: {clean_line}\n")
                        logfile.flush()

                    if any(keyword in clean_line for keyword in ["EVENT", "REJECT", "INIT", "STATUS", "Forwarding"]):

                        # Remove and reset for clean input lines
                        print("\r" + " " * 90 + "\r", end="", flush=True)

                        # Print telemetry to terminal
                        print(f"[{timestamp}] RECEIVED TM: {clean_line}", flush=True)

                        # Input prompt
                        print("Ground-MCS> ", end="", flush=True)
    except Exception as e:
        print(f"\n[GROUND] Error in receiving thread: {e}")

def run_ground():
    print("[GROUND] Connecting to Platform OBC...")
    gnd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        gnd_socket.connect((PF_HOST, PF_PORT))
        print("[GROUND] Successfully connected to Satellite!")

        with open("HouseKeeping_log.txt", "w") as logfile:
            logfile.write(f"--- NEW SATELLITE SESSION STARTED [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] ---\n")
        print("[GROUND] HouseKeeping_log.txt has been cleaned and refreshed.")

    except ConnectionRefusedError:
        print("[GROUND] ERROR: Platform OBC is not running.")
        return

    # START the BACKGROUND Thread =======================================================
    TM_thread = threading.Thread(target=recv_TM_thread, args=(gnd_socket,), daemon=True)
    TM_thread.start()

    print("Write Command:\n")

    # MAIN Loop =========================================================================
    while True:
        cmd = input("Ground-MCS> ").strip()
        if not cmd:
            continue
        full_cmd = f"{cmd}\n"

        try:
            gnd_socket.sendall(full_cmd.encode('utf-8'))
        except:
            print("[GROUND] Could not send Command!")
            break

        if cmd.lower() == 'exit':
            print("[GROUND] Shutting Down...")
            break

    gnd_socket.close()

if __name__ == "__main__":
    run_ground()
