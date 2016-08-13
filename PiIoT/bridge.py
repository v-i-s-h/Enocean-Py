# Bridge.py
import sys, os, inspect
import time
from time import gmtime, strftime

# Add modules to path
libPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "./../"))
if libPath not in sys.path:
    sys.path.insert(0, libPath)

from EnoceanPy import EO
from EnoceanPy import ESP

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

basePath    = 'usr/vish/'
appPath     = 'sensors/'

## Define MQTT callbacks
def onConnect( client, userData, retCode ):
    client.publish( basePath+'devices/enocean', '{"name":"enocean gateway","desc":"ESP to MQTT bridge"}' );


def main():
    print "\t\t**    Enocean bridge     **"
    
    ttyPort = "/dev/ttyAMA0"
    print "\tEncoean gateway port : " + ttyPort + '\n'

    # CO_RD_IDBASE command
    cmd1 = [ 0x55, 0x00, 0x01, 0x00, 0x05, 0x70, 0x08, 0x38 ]

    hEOGateway = EO.connect( ttyPort )
    # better to wait a little for connection to establish
    time.sleep( 0.100 )

    ## display any packets already in buffer
    print "Buffered Packets : ",
    rawResp = EO.receiveData( hEOGateway )
   
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

    # Connect to broker
    client = mqtt.Client( client_id = "enocean_bridge",
                            clean_session = True );
    client.on_connect = onConnect;
    client.connect( "192.168.1.54", 1883, 60 )
    client.loop_start();

    try:
        while( True ):
            rawResp = EO.receiveData( hEOGateway )
            if rawResp:
                print strftime("%Y-%m-%d %H:%M:%S",gmtime()),": ",
                print '[RXD] ',
                for i in range( len( rawResp ) ):
                    print "%02X" %(rawResp[i]),
                print ''
                pkts = ESP.decodeRawResponse( rawResp )
                for pkt in pkts:
                    # print "    :> ",
                    # for i in range(len(pkt['data_recv'])):
                    #     print "%02X" %(pkt['data_recv'][i]),
                    # print ''
                #     print "[PACKET]................................................................."
                    telegram = ESP.decodeRadioData( pkt )
                    if( telegram['dev'] != 'UNKN' ):    # Not an unknown telelgram
                        mqttPacket = {}
                        str_id = ""
                        for i in telegram['id']:
                            str_id = str_id + ("%02X" %i)
                        mqttPacket['id'] = str_id;
                        # Check which sensor send the telegram
                        if telegram['dev'] == 'RCKR':
                            # From rocker swicth
                            action  = telegram['data'] & 0xE0
                            bow     = telegram['data'] & 0x10
                            if bow == 0x10:
                                if action == 0x00:
                                    mqttPacket['action'] = 'AI'
                                elif action == 0x01:
                                    mqttPacket['action'] = 'A0'
                                elif action == 0x20:
                                    mqttPacket['action'] = 'BI'
                                elif action == 0x30:
                                    mqttPacket['action'] = 'B0'
                                else:
                                    print "%02X" %action
                                    mqttPacket['action'] = 'invalid'
                            else:
                                mqttPacket['action'] = 'released'
                        elif telegram['dev'] == 'TEMP':     # From temperature sensor
                            # 3rd byte in data is useful
                            mqttPacket['temp'] = 20.0 + (60.0-20.0)/255*telegram['data'][2]
                        elif telegram['dev'] == 'CNCT':
                            mqttPacket['status'] = telegram['data']&0x01;

                        str_mqtt = ', '.join("%s=%r" % (key,val) for (key,val) in mqttPacket.iteritems())
                        print( str_mqtt )
                        client.publish( basePath+appPath+str_id, str_mqtt );
                # print "........................................................................."
    except KeyboardInterrupt:
        print "\nExiting Enocean MQTT Brdige"
        EO.disconnect( hEOGateway )
        client.disconnect()
main()