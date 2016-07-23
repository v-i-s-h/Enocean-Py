#  eopy.py -- Demo application for Enocean Py API
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


import time

import EO
import ESP

'''
Function    : main
Description : main function
Arguments   : none
Returns     : none
'''
def main():
    print "\t\t*************************************************"
    print "\t\t**    Enocean Py - Monitor Enocean devices     **"
    print "\t\t*************************************************"
    ttyPort = "/dev/ttyS0"
    print "\tUsing serial port : " + ttyPort + '\n'
    
    # CO_RD_VERSION command
    cmd0 = [ 0x55, 0x00, 0x01, 0x00, 0x05, 0x70, 0x03, 0x09 ]
    # CO_RD_IDBASE command
    cmd1 = [ 0x55, 0x00, 0x01, 0x00, 0x05, 0x70, 0x08, 0x38 ]
    
    hEOGateway = EO.connect( ttyPort )
    # better to wait a little for connection to establish
    time.sleep( 0.100 )
    
    ## display any packets already in buffer
    print "Buffered Packets : ",
    rawResp = EO.receiveData( hEOGateway )
    if rawResp:
        print ''
        print 'RECEIVED :',
        for i in range( len( rawResp ) ):
            print "%02X" %(rawResp[i]),
        print ''
        pkts = ESP.decodeRawResponse( rawResp )
        for pkt in pkts:
            print "[PACKET]................................................................."
            ESP.displayPacketInfo( pkt )
        print "........................................................................."
    else:
        print"\t[NONE]"
    ## Send CO_RD_VERSION
    print "RQST       : ",
    for i in range( len( cmd0 ) ):
        print "%02X" %( cmd0[i] ),
    print ''
    rawResp = EO.sendData( hEOGateway, cmd0 )
    print 'RESP(%3dB) : ' %len( rawResp ),
    for i in range( len( rawResp ) ):
        print "%02X" %(rawResp[i]),
    print ''
    pkt = ESP.decodePacket( rawResp )
    ESP.displayPacketInfo( pkt, 'CO_RD_VERSION' )
    
    ## Send CO_RD_IDBASE
    print "RQST       : ",
    for i in range( len( cmd1 ) ):
        print "%02X" %( cmd1[i] ),
    print ''
    #~ EO_receiveData( hEOGateway )        # Read any buffered data
    rawResp = EO.sendData( hEOGateway, cmd1 )
    print 'RESP(%3dB) : ' %len( rawResp ),
    for i in range( len( rawResp ) ):
        print "%02X" %(rawResp[i]),
    print ''
    pkt = ESP.decodePacket( rawResp )
    ESP.displayPacketInfo( pkt, 'CO_RD_IDBASE' )
    
    try:
        while( True ):
            rawResp = EO.receiveData( hEOGateway )
            if rawResp:
                print 'RECEIVED :',
                for i in range( len( rawResp ) ):
                    print "%02X" %(rawResp[i]),
                print ''
                pkts = ESP.decodeRawResponse( rawResp )
                for pkt in pkts:
                    print "[PACKET]................................................................."
                    ESP.displayPacketInfo( pkt )
                print "........................................................................."
    except KeyboardInterrupt:
        print "\nExiting Enocean Py Demo"
        EO.disconnect( hEOGateway )
        print "Bye..bye.. :) "
    
if __name__ == "__main__":
    main()
