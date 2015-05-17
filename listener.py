# -*- coding: utf-8 -*-
"""
@author: Eva Kraegeloh
"""

import time
import socket
import cloudant
import pynedm
import signal
import string

from ADAM6015 import *
from lakeshore218 import *
from deltaElectronica import *
from hamegHMP4040 import *
from ADAM6224 import *
from webAdio_telnet import *


buf = 1024

#handling strg-c
_should_quit = False

def sigint_handler(signum, frame):
    global _should_quit
    print "Handler received termination signal", signum
    _should_quit = True

signal.signal(signal.SIGINT, sigint_handler)

#database stuff
#acct = cloudant.Account(uri="http://raid.nedm1:5984")
#res = acct.login("hexe_edm", "clu$terXz")
#assert res.status_code == 200
#db = acct["nedm%2Fhexe_edm"] #grab hexe database
#des = db.design("nedm_default")

_server = "http://raid.nedm1:5984/"
_un = "hexe_edm"
_pw = "clu$terXz"
_db = "nedm%2Fhexe_edm"

po = pynedm.ProcessObject(_server, _un, _pw, _db)


adam_tempIP = '192.168.1.64'
adam_tempPort = '1025'

lsIP = '192.168.1.51'
lsPort = '100'

deltaIP = '192.168.1.70'
deltaPort = '8462'

hamegIP = '192.168.1.51'
hamegPort = '300'

adam_aoIP = '192.168.1.67'
adam_aoPort = '1025'

##WEBADIO configuration
#IP adress of the IPSES WEB-ADIO board
webadioIP = '192.168.1.65'
webadioPW = 'ipses'


func_dict = {
	'set_oven:temp' : set_heater_power,
	'set_oven_flow' : set_heater_flow,
	'set_laser_status' : set_laser_status,
	'set_laser_current' : set_laser_current,
	'set_coil_status' : set_coil_status,
	'set_coil_current' : set_coil_current,
	'set_ramp_time' : set_ramp_time,
	'enable_high_voltage' : hv_state,
	'set_high_voltage' : set_high_voltage,
	'send_pulse' : send_nmr_pulse,
	'field_switch' : field_switch,
	'magnicon_to' : set_magnicon_status,
	'cryo_cooler' : cryo_cooler
	}

adoc = {
	"type": "data", "value": {}
	}

adamT = adam_reader()
adamT_connected = False
if adamT.connect(adam_tempIP, adam_tempPort): adamT_connected = True

lakesh = lakeshore()
lakesh_connected = False
if lakesh.connect(lsIP, lsPort): lakesh_connected = True

delta = delta_supply()
delta_connected = False
if delta.connect(deltaIP, deltaPort):
	delta_connected = True
	init_laser()

hameg = hameg_supply()
hameg_connected = False
if hameg.open_socket(hamegIP, hamegPort): hameg_connected = True

adamAO = adam_setter()
adamAO_connected = False
if adamAO.connect(adam_aoIP, adam_aoPort):
	adamAO_connected = True
	adamAO.set_ranges()
	adamAO.zero_all_ao()

adio = webadio()
adio_connected = False
if adio.login(webadioIP, webadioPW):
	adio_connected = True
	dig_init()


db_listener = pynedm.listen(execute_dict, _db
              username=_un, password=_pw, uri=_server)


while True:

	adam_temps = adamT.read_temp()
	for Tname in adam_temps:
		adoc["value"][Tname] = float(adam_temps[Tname])

	ls_values = lakesh.read_values()
	for key in ls_values:
		adoc["value"][key] = float(ls_values[key])

	current = delta.read_current()
	state = delta.read_output_state()
	#print "---Monitor---\nVoltage: " + delta.read_voltage() + "\nCurrent: " + current
	adoc['value']['laser_current'] = float(current)
	adoc['value']['laser_status'] = int(state)

	coil_dict = read_coil_currents()
	for coil in coil_dict:
		adoc["value"][coil] = float(coil_dict[coil])

	ao_values = read_aos()
	for aos in ao_values:
		adoc["values"][aos] = float(ao_values[aos])

	adio_values = filter_db_values()
	for vals in adio_values:
		adoc["value"][vals] = float(adio_values[vals])


	po.write_document_to_db(adoc)
	time.sleep(2)
    if pynedm.should_stop(): break


print "Quitting script..."
#wait for listener to stop
po.wait()
print "listening stopped"
#close  connections
adamT.disconnect()
lakesh.disconnect()
delta.disconnect()
hameg.close_socket()
adamAO.disconnect()
adio.close()
print "All connections closed."


