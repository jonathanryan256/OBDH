import socket
import time

PF_HOST = '127.0.0.1'
PF_PORT = 5001
PL_PORT = 5002

def run_platform():
    # Try to connect to the payload (the payload must already be turned ON).
    print("[PLATFORM] is connecting to Payload...")
    pl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try: 
            pl_socket.connect((PF_HOST, PL_PORT))
            print("[PLATFORM] is succesfully connected to Payload.")
            break
        except ConnectionRefusedError:
            print("[PLATFORM] is non-active, wait 2 seconds...")
            time.sleep(2)

    # Start the server for the ground station.
    pf_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)