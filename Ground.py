import socket
import threading
import time
from datetime import datetime

PF_HOST = '127.0.0.1'
PF_PORT = 5001

def generateTimeFromhhmmss(hour,minute,second): #For scheduling commands
    t = time.localtime()
    return time.mktime(time.struct_time((t.tm_year,t.tm_mon,t.tm_mday,int(hour),int(minute),int(second),0,0,0)))

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
    commandList = ["exit","payload take-image", "mode_status","set-mode safe","set-mode target","payload power-on","payload power-off","set_time","schedule_command"]
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
    timeSet = False
    # MAIN Loop =========================================================================
    while True:
        cmd = input("Ground-MCS> ").strip()
        if not cmd:
            continue
        if cmd == "SET_TIME":
            timeSet = True
        if cmd not in commandList:
              print(f"PF_TIM: REJECT - Unknown command: '{cmd}'. Nothing processed.\n")
 
        if cmd == "SET_TIME": #Current time needs to be sent to Platform
            cmd = cmd+str(time.mktime(time.localtime()))
        if cmd == "SCHEDULE_COMMAND":
            if timeSet:
                scheduledCommand = input("Enter command to be Scheduled: ").strip()
                scheduledTime = input("Enter scheduled time in hh:mm:ss: ").strip()
                [hh,mm,ss] = scheduledTime.split(":")
                trgtTime = generateTimeFromhhmmss(hh,mm,ss) #converts time to time since epoch
                cmd = cmd + "," +  scheduledCommand + "," + str(trgtTime)
            else:
                print("TIME IS NOT SET YET, SET TIME BEFORE SCHEDULING")
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
