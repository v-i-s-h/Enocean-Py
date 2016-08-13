#  tests.py -- tests for ESP module
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


import EO
import ESP

'''
Function    :
Description :
Arguments   :
Returns     :
'''

'''
Function    : main
Description : main function
Arguments   : none
Returns     : none
'''
def main():
    
    ttyPort = "/dev/ttyACM0"
    
    # Test Data 1 : Command Read Version
    testData = [ 0x55, 0x00, 0x01, 0x00, 0x05, 0x70, 0x03, 0x09 ]
    print "RAW DATA   : ",
    for i in range( len( testData ) ):
        print "%02X" %( testData[i] ),
    print ''
    pkt = ESP.decodePacket( testData )
    ESP.displayPacketInfo( pkt, 'CO_RD_VERSION' )
    
    # Test Data 2 : Response for COMMON_COMMAND CO_RD_VERSION
    testData = [ 0x55,
                 0x00, 0x21, 0x00, 0x02,
                 0x26,
                 0x00, 0x02, 0x07, 0x01, 0x00, 0x02, 0x04, 0x02,
                 0x01, 0x00, 0x84, 0x23, 0xCC, 0x45, 0x4F, 0x01,
                 0x03, 0x47, 0x41, 0x54, 0x45, 0x57, 0x41, 0x59,
                 0x43, 0x54, 0x52, 0x4C, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0xA3 ]
    print "RAW DATA   : ",
    for i in range( len( testData ) ):
        print "%02X" %( testData[i] ),
    print ''
    pkt = ESP.decodePacket( testData )
    ESP.displayPacketInfo( pkt, 'CO_RD_VERSION' )
    
    # Response for CO_RD_BASE_ID
    testData = [ 0x55,
                 0x00, 0x05, 0x01, 0x02,
                 0xDB,
                 0x00, 0xFF, 0x91, 0xE6, 0x00,
                 0x0A,
                 0xFC ]
    print "RAW DATA   : ",
    for i in range( len( testData ) ):
        print "%02X" %( testData[i] ),
    print ''
    pkt = ESP.decodePacket( testData )
    ESP.displayPacketInfo( pkt, 'CO_RD_IDBASE' )
    
    # Test data 4 : Response from Rocker Switch
    testData = [ 0x55,
                 0x00, 0x07, 0x07, 0x01,
                 0x7A,
                 0xF6, 0x50, 0x00, 0x1A, 0x34, 0x82, 0x30,
                 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x2B, 0x00,
                 0x5E ]
    print "RAW DATA   : ",
    for i in range( len( testData ) ):
        print "%02X" %( testData[i] ),
    print ''
    pkt = ESP.decodePacket( testData )
    ESP.displayPacketInfo( pkt )
    
    # decode multiple packets
    testData = [ 
                 # Response from Rocker switch
                 0x55,
                 0x00, 0x07, 0x07, 0x01,
                 0x7A,
                 0xF6, 0x50, 0x00, 0x1A, 0x34, 0x82, 0x30,
                 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0x2B, 0x00,
                 0x5E,
                 # Response for COMMON_COMMAND CO_RD_VERSION
                 0x55,
                 0x00, 0x21, 0x00, 0x02,
                 0x26,
                 0x00, 0x02, 0x07, 0x01, 0x00, 0x02, 0x04, 0x02,
                 0x01, 0x00, 0x84, 0x23, 0xCC, 0x45, 0x4F, 0x01,
                 0x03, 0x47, 0x41, 0x54, 0x45, 0x57, 0x41, 0x59,
                 0x43, 0x54, 0x52, 0x4C, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0xA3,
                ]
    
    packets = ESP.decodeRawResponse( testData )
    print "Test for decoding multiple packets : "
    for packet in packets:
        print "[PACKET]................................................................."
        ESP.displayPacketInfo( packet, 'CO_RD_VERSION' )
if __name__ == "__main__":
    main()
