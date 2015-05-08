#! /usr/bin/env python

import time
import socket
import cloudant
import pynedm
import signal
import string

#creating socket via TCP:
buf = 1024
tcp=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.connect(('192.168.1.51', 300))
tcp.send("*IDN?\n")
time.wait(0.1)
print "Connected to " + tcp.recv(buf)
tcp.send("*RST\n")
time.wait(0.1)
print "Device reset."
tcp.send("SYST:REM\n")

#handling strg-c
_should_quit = False

def sigint_handler(signum, frame):
    global _should_quit
    print "Handler received termination signal", signum
    _should_quit = True

signal.signal(signal.SIGINT, sigint_handler)

#database stuff
acct = cloudant.Account(uri="http://raid.nedm1:5984")
res = acct.login("hexe_edm", "clu$terXz")
assert res.status_code == 200
db = acct["nedm%2Fhexe_edm"] #grab hexe database
des = db.design("nedm_default")

class hameg-power-supply:

    def __init__(self, channel)
        self.channel = int(channel)
        tcp.send("INST OUT" + str(self.channel) + "\n")
        time.wait(0.1)
        tcp.send("OUTP:SEL ON\n")

    def read_volt(self):
        tcp.send("MEAS:VOLT?\n")
        return string.rstrip(tcp.recv(buf))

    def read_curr(self):
        tcp.send("MEAS:CURR?\n")
        return string.rstrip(tcp.recv(buf))

    def set_volt_max(self):
        tcp.send("VOLT MAX\n")
        tcp.send("*WAI\n")
        return

    def read_volt_max(self):
        tcp.send("VOLT? MAX\n")
        return string.rstrip(tcp.recv(buf))

    def read_curr_max(self):
        tcp.send("CURR? MAX\n")
        return string.rstrip(tcp.recv(buf))

    def set_curr(self, curr):
        tcp.send("CURR " + str(curr) + "\n")
        tcp.send("*WAI\n")
        tcp.send("CURR?\n")
        response = float(string.rstrip(tcp.recv(buf)))
        if response != curr:
            raise ValueError("Not able to set current!")
        else:
            return

    def set_output(self, state):
        if int(state) == 1: tcp.send("OUTP ON\n")
        else: tcp.send("OUTP OFF\n")
        return

    def get_output(self):
        tcp.send("OUTP?\n")
        return string.rstrip(tcp.recv(buf))

    def ramp(self, datastring):
        tcp.send("ARB:CLEAR\n")
        if datastring == "up":
            tcp.send("ARB:REST 1\n")
        elif datastring == "down":
            tcp.send(" ARB:REST 2\n")
        else:
            tcp.send("ARB:DATA " + string.rstrip(datastring) + "\n")
        tcp.send("*WAI\n")
        tcp.send("ARB:REP 1\n")
        tcp.send("ARB:TRAN " + str(self.channel) + "\n")
        tcp.send("*WAI\n")
        tcp.send("OUTP ON\n")
        tcp.send("ARB:START " + str(self.channel) + "\n")

#dictionary for coil-channel-relation
coilchannel = {"pol" : 1, "trans" : 3, "guide" : 4}

#variables for coil currents and ramp time, initialized with standard values
coil_currents = {1 : 3.1, 2 : 0.0, 3 : 3.1, 4 : 3.1}
ramp_time = 10 #in s

def set_current(coil, value):
    coil_currents[coil] = value
    return

def set_ramp_time(t):
    ramp_time = t
    return

def set_status(coil, state):
    ch = coilchannel[coil]
    hameg=c[ch-1]
    if ch == 1:
        hameg.set_curr(coil_currents[ch])
        hameg.set_output(state)
        time.wait(0.1)
        if hameg.get_output() != state:
            raise Exception('Not able to change status!')
        else: return
    else:
        n = 128 #no of data points for abitrary wave form
        stay_time = float(ramp_time)/128
        if stay_time < 0.01: #min time at one point 10ms
            n = int(float(ramp_time)/0.01)
            stay_time = float(ramp_time)/n
        elif stay_time > 60: #max time at one point 60s
            raise Exception('Ramp time too long!')
        curr_step = float(coil_currents[ch])/n
        data_string = ""
        data = []
        i = 0
        while i <= n:
            data.append(32)
            data.append(i*curr_step)
            data.append(stay_time)
            i = i+1
        if state == 1:
            j = 0
            while j < len(data)-1:
                data_string = data_string + str(data[j]) + ","
            data_string = data_string + str(data[-1])
        else:
            j = len(data)-1
            while j > 0:
                data_string = data_string + str(data[j]) + ","
            data_string = data_string + str(data[0])
        hameg.ramp(data_string)
        if state == 0:
            time.wait(n*stay_time)
            hameg.set_output(0)
        return

pol = hameg-power-supply(1)
trans = hameg-power-supply(3)
guide = hameg-power-supply(4)
c = [pol, 0, trans, guide]

func_dic = {
    "set_coil_current" : set_current,
    "set_coil_status" : set_status,
    "set_ramp_time" : set_ramp_time
    }

adoc = {
    'type':'data',
    'value':{
        'pol_coil_current':0,
        'trans_coil_current':0,
        'guide_coil_current':0
         }
    }

pynedm.listen(
    db_func_dict,
    "nedm%2Fhexe_edm",
    uri="http://rais.nedm1:5984",
    username="hexe_edm",
    password="clu$terXz"
    )

while True:
    pol_curr = pol.read_curr()
    trans_curr = trans.read_curr()
    guide_curr = guide.read_curr()
    print "---Monitor---\nPolarizer coil current: "  + pol_curr + "\nTransport coil current: " + trans_curr + "\nGuide coil current: " + guide_curr
    adoc['value']['pol_coil_current'] = float(pol_curr)
    adoc['value']['trans_coil_current'] = float(trans_curr)
    adoc['value']['guide_coil_current'] = float(guide_curr)
    des.post("_update/insert_with_timestamp",params=adoc).json()
    time.sleep(2)
    if pynedm.should_stop(): break

print "Quitting script..."
pynedm.wait()
print "Listening stopped."
tcp.close()
print "Connections closed."

