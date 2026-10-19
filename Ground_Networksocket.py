import socket
from datetime import datetime


PF_HOST = '127.0.0.1'
PF_PORT = 5001

def run_ground():
    # Try to connect to the platform
    print("[GROUND] Connecting with Platform OBC...")
    gnd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        gnd_socket.connect((PF_HOST, PF_PORT))
        print("[GROUND] Connected with the Satellite!")
    except ConnectionRefusedError:
        print("[GROUND] FAILURE: Platform OBC is Non-active.")
        return

    print("Write command:")

    # Command loop for Ground =====================================================
    while True:
        # Ask for input from User.
        cmd = input("Ground-MCS> ")
        if not cmd:
            continue

        # Send command.
        gnd_socket.send(cmd.encode('utf-8'))

        # Shut down the telecommunication.
        if cmd.lower() == 'exit':
            print("[GROUND] Shutting down...")
            break

        # Wait on telemetry answer
        telemetry = gnd_socket.recv(1024).decode('utf-8')

        # Add a ground timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] RECEIVED TM: {telemetry}")

    gnd_socket.close()

if __name__ == "__main__":
    run_ground()