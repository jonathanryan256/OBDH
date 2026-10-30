import socket
import time
from datetime import datetime


PF_HOST = '127.0.0.1'
PF_PORT = 5001
PL_PORT = 5002
currentTime =0
sleptTime = 0
processStatus = [0,0,0,0,0,0,0,0]
processFunction = [0,0,0,0,0,0,0,0]
processTime = [0,0,0,0,0,0,0,0]
index = 0

index = 0 #initial process number for scheduling - can be 0-7
def doAtTime(function,t):
    global currentTime
    #print(function)
    print(t-currentTime, function)
    if currentTime>=t:
        return function
    else:
        return "Waiting"
    
def scheduleFunction(function, time,processIndex):
    global processStatus
    #global processPin
    global processFunction
    global processTime
    processStatus[processIndex] = 1
    #processPin[processIndex] = 0
    processFunction[processIndex] = function
    processTime[processIndex] = time

def sleep(t): # For timekeeping the amount of time spent sleeping must be tracked. Use this function instead of time.sleep()
    global sleptTime
    time.sleep(t) 
    sleptTime += t


def run_platform():
    command = ""
    global processStatus
    global processFunction
    global processTime
    global index
    global currentTime
    global sleptTime
    timeIsSet = False
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
            print("[PLATFORM] Non-active, please wait...")
            sleep(1)

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

    # OBT & HouseKeeping Configuration =====================================================
    boot_time = time.time()
    lastHKtime = time.time()
    HK_interval = 5 # Automatically send HK data every x seconds.

    gnd_conn.settimeout(0.1)

    print(f"\n[PLATFORM] Status: [{current_mode}] | Payload: [{payload_power}] | Waiting for ground...")

    # Run through command loop =============================================================
    while True:
        #print("start of loop")
        #Command scheduling
        scheduleCommandString = ""
        command = ""
        for i in range(0,len(processStatus)): #running schuduled commands
            if processStatus[i]==1:
                #print("process " + processFunction[i] + " waiting" + " on slot " ,str(i))
                aString = doAtTime(processFunction[i],processTime[i])
                if aString != "Waiting":
                    processFunction[i]=0
                    processStatus[i]=0
                    processTime[i]=0
                    scheduleCommandString = scheduleCommandString+aString
                    print("Executing command: ", aString)          
        if timeIsSet:
            currentTime = time.process_time()+timeOffset+sleptTime
        else:
            currentTime = time.process_time()
        #gnd_conn.settimeout(1)
        
        # Cyclical loop for keeping track of HouseKeeping data.
        current_time = time.time()
        if current_time - lastHKtime >= HK_interval:
            # Calculate the OBT (SCET).
            total_sec = int(current_time - boot_time)
            hours = (total_sec // 3600) %24
            minutes = (total_sec // 60) %60
            seconds = total_sec %60
            SCET_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Build HK-package
            HK_packet = f"PF_TM: HK_CYCLIC | OBT=[{SCET_time}] | PF_MODE=[{current_mode}] | PL_POWER=[{payload_power}]\n"

            try:
                gnd_conn.sendall(HK_packet.encode('utf-8'))
                print(f"[PLATFORM] Cyclic HouseKeeping data transmitted at {SCET_time}")
            except:
                pass # Do NOT crash when ground station is disconnected

            lastHKtime = current_time

        # Reconnect when interrupted & Listen to Commands ========================================
        try:
            command = gnd_conn.recv(1024).decode('utf-8').strip()
            #if not command:
            #    continue
        except socket.timeout:
            sleptTime = sleptTime+0.1
            #command = "" #must be set 
            #continue
        except (ConnectionResetError, ConnectionAbortedError):
            print("[PLATFORM] Lost connection with Ground. Waiting for reconnection...")
            gnd_conn, gnd_addr = pf_server.accept()
            gnd_conn.settimeout(0.1)
            print(f"\n[PLATFORM] Status: [{current_mode}] | Payload: [{payload_power}] | Waiting for ground...")
            continue
        
        # Shut Down system if exit is requested.
        if command.lower() == 'exit':
            print("[PLATFORM] Shutdown signal received, Shutting Down...")
            pl_socket.sendall("exit".encode('utf-8'))
            break
        if command !="":
            print(f"[PLATFORM] Received from Ground -> '{command}'")


        # =====================================================================================
        # COMMANDS PROCESSING
        # =====================================================================================
        #print(scheduleCommandString, " is the current scheduleCommandString")
        # Show MODE ===========================================================================
        if command[0:8] == "SET_TIME":
            localTime = float(command[8:])
            sleptTime = 0 #Reset this, it is accounted for in "timeOffset" in the next line
            timeOffset = localTime-time.process_time() #add offset and timeSlept to process_time to get current locat time in time since epoch
            timeIsSet = True
        if command == "REPORT_MODE" or "REPORT_MODE" in scheduleCommandString:
            #print('SOIDJFDO')
            reply = f"PF_TM: STATUS - Current mode is [{current_mode}], (Payload is {payload_power})\n"
            gnd_conn.sendall(reply.encode('utf-8'))

        if "SCHEDULE_COMMAND" in command or "SCHEDULE_COMMAND" in scheduleCommandString: # this must be before the elif
            [scheduleCommand, cmd, trgtTime] = command.split(",")
            trgtTime = float(trgtTime)
            if timeIsSet:
                if trgtTime <currentTime:
                    print("TIME has already passed")
                else:
                    scheduleFunction(cmd,trgtTime,index)
                    print(cmd + "Scheduled for ", str(trgtTime) + "current time is " + str(currentTime))
                    index = (index+1)%8 # index cycles through all indices and then resets back to zero
            else:
                print("time is not set, cannont schedule")
        # Swap-MODE Logic ===================================================================
        if "SET-MODE" == command or "SET-MODE" in scheduleCommandString:
            if "SET-MODE" in command:
                new_mode = command.replace("SET-MODE ", "").upper()
            elif "SET-MODE" in scheduleCommandString:
                if "SAFE" in scheduleCommandString:
                    new_mode = "SAFE"
                elif "TARGET" in scheduleCommandString:
                    new_mode = "TARGET"
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
                    
                    sleep(3)

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
            

            continue
            

        # Commands for PAYLOAD ================================================================
        if ("PAYLOAD" in command and "SCHEDULE_COMMAND" not in command) or "PAYLOAD" in scheduleCommandString:

            # Reject any command when SAFE-MODE is active.
            if current_mode == "SAFE":
                reply = "PF_TM: REJECT - Payload command rejected. Current mode = SAFE\n"
                gnd_conn.sendall(reply.encode('utf-8'))
                continue

            # When mode is not SAFE we continue with the payload commands.
            sendCommand = ""
            if "POWER-ON" in command or "POWER-ON" in scheduleCommandString:
                payload_power = "ON"
                sendCommand = "PAYLOAD POWER-ON"
            elif "POWER-OFF" in command or "POWER-OFF" in scheduleCommandString:
                payload_power = "OFF"
                sendCommand = "PAYLOAD POWER-OFF"
            elif "TAKE-IMAGE" in command or "TAKE-IMAGE" in scheduleCommandString:
                sendCommand = "PAYLOAD TAKE-IMAGE"
            
            # Forward command to payload.
            print("[PLATFORM] Forwarding command to Payload...")
            pl_socket.sendall(sendCommand.encode('utf-8'))

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

        #else:
        #    reply = f"PF_TIM: REJECT - Unknown command: '{command}'. Nothing processed.\n"
        #    gnd_conn.sendall(reply.encode('utf-8'))
        #    print(f"[PLATFORM] Command rejected: '{command}' is invalid.")

    # Shut down server ======================================================================
    print("[PLATFORM] Server shutting down...")
    gnd_conn.close()
    pf_server.close()
    pl_socket.close()

if __name__ == "__main__":
    run_platform()

