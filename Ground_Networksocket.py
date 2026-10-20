import socket
from datetime import datetime

logFilePath = "logfile.txt"
PF_HOST = '127.0.0.1'
PF_PORT = 5001
def printToLogFile(string):
    with open(logFilePath,"a") as fid:
            print(string, file=fid)

def run_ground():
    
    # Clear log file at startup
    with open(logFilePath, "r+") as fid:
        fid.seek(0)
        fid.truncate()

    # Try to connect to the platform
    print("[GROUND] Connecting with Platform OBC...")
    gnd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        gnd_socket.connect((PF_HOST, PF_PORT))
        str = "[GROUND] Successfully connected to satellite!"
        print(str)
        printToLogFile(str)
    except ConnectionRefusedError:
        str = "[GROUND] ERROR: Platform OBC is not running."
        print(str)
        printToLogFile(str)
        return

    print("Write command:")



    # Command loop for Ground =====================================================
    while True:
        # Ask for input from User.
        cmd = input("Ground-MCS> ").strip()
        if not cmd:
            continue

        # Send command to platform.
        gnd_socket.send(cmd.encode('utf-8'))

        # Shut down the telecommunication.
        if cmd.lower() == 'exit':
            str = "[GROUND] Shutting down..."
            print(str)
            printToLogFile(str)
            break

        buffer = ""
        printed_lines = set()
        while True:
            command = gnd_socket.recv(1024).decode('utf-8')
            if not command:
                break

            buffer += command
            if buffer:
                # Split the message at \n
                lines = buffer.split("\n")

                for line in lines:
                    clean_line = line.strip()

                    if clean_line and clean_line not in printed_lines:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        str = f"[{timestamp}] RECEIVED TM: {line.strip()}"
                        print(str)
                        printToLogFile(str)
                        printed_lines.add(clean_line)

                if any(x in buffer for x in ["EVENT", "REJECT", "STATUS", "Forwarding"]):
                    break

    gnd_socket.close()

if __name__ == "__main__":
    run_ground()