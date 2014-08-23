#  EO.py -- Module for managing device connections
#  
#  Copyright 2014 Vishnu Raj <rajvishnu90@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  


import serial
import os
import time
import sys

'''
Function    : EO_connect
Description : Connect to Enocean Gateway device
Arguments   : 1
              portID - port name to which gateway device is connected
Returns     : a handle to port, if success.
'''
def connect( portID ):
    hDevice = None
    hDevice = serial.Serial( portID, 57600, timeout = 0 )
    return hDevice

'''
Function    : EO_sendData
Description : Acts as the interface to EnOcean gateway device
Arguments   : 2
              hSerial - handle to serial port to which device is connected
              rawData - data to send as list in raw ( number, base:dec ) format
Returns     : stream of raw data received as response, empty list if no response
'''

def sendData( hSerial, rawData ):
    for idx in range( len( rawData ) ):
        hSerial.write( chr(rawData[idx]) )
    time.sleep( 0.10 )
    rawResp = receiveData( hSerial )
    return rawResp

'''
Function    : EO_receiveData
Description : Acts as the read interface to EnOcean gateway device
Arguments   : hSerial - handle to serial port to read from
Returns     : stream of raw data read, empty list if nothing read
'''
def receiveData( hSerial ):
    data = []
    while hSerial.inWaiting() != 0:
        #~ data.append( hSerial.read(1).encode("hex") )
        data.append( ord(hSerial.read(1)) )
        time.sleep( 0.001 )
    return data

'''
Function    : EO_disconnect
Description : closes the connection to EO gateway
Arguments   : hSerial - handle to serial port to close connection
Returns     : none
'''
def disconnect( hSerial ):
    hSerial.close()
