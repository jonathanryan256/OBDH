import socket
from datetime import datetime
import time

logFilePath = "Logfile.txt"
PF_HOST = '127.0.0.1'
PF_PORT = 5001

def generateTimeFromhhmmss(hour,minute,second): #For scheduling commands
    t = time.localtime()
    return time.mktime(time.struct_time((t.tm_year,t.tm_mon,t.tm_mday,int(hour),int(minute),int(second),0,0,0)))

def printToLogFile(string):
    with open(logFilePath,"a") as fid:
            print(string, file=fid)

def run_ground():
    
    # Clear log file at startup
    
    with open(logFilePath, "w+") as fid:
        fid.seek(0)
        fid.truncate()

    # Try to connect to the platform
    print("[GROUND] Connecting with Platform OBC...")
    gnd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        gnd_socket.connect((PF_HOST, PF_PORT))
        printStr= "[GROUND] Successfully connected to satellite!"
        print(printStr)
        printToLogFile(printStr)
    except ConnectionRefusedError:
        printStr= "[GROUND] ERROR: Platform OBC is not running."
        print(printStr)
        printToLogFile(printStr)
        return

    print("Write command:")



    # Command loop for Ground =====================================================
    while True:
        # Ask for input from User.
        cmd = input("Ground-MCS> ").strip()
        if not cmd:
            continue
        if cmd == "SET_TIME": #Current time needs to be sent to Platform
            cmd = cmd+str(time.mktime(time.localtime()))
        if cmd == "SCHEDULE_COMMAND":
            scheduledCommand = input("Enter command to be Scheduled: ").strip()
            scheduledTime = input("Enter scheduled time in hh.mm.ss: ").strip()
            [hh,mm,ss] = scheduledTime.split(".")
            trgtTime = generateTimeFromhhmmss(hh,mm,ss) #converts time to time since epoch
            cmd = cmd + "," +  scheduledCommand + "," + str(trgtTime)

        # Send command to platform.
        gnd_socket.send(cmd.encode('utf-8'))
        
        # Shut down the telecommunication.
        if cmd.lower() == 'exit':
            printStr= "[GROUND] Shutting down..."
            print(printStr)
            printToLogFile(printStr)
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
                        printStr= f"[{timestamp}] RECEIVED TM: {line.strip()}"
                        print(printStr)
                        printToLogFile(printStr)
                        printed_lines.add(clean_line)

                if "INIT" in buffer:
                    if "EVENT" in buffer:
                        break
                    else:
                        continue

                if any(x in buffer for x in ["EVENT", "REJECT", "STATUS", "Forwarding"]):
                    break

    gnd_socket.close()

if __name__ == "__main__":
    run_ground()