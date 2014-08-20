import serial
import os
import time
import sys

'''
ESP3 packet structure through the serial port.
Protocol bytes are generated and sent by the application

Sync = 0x55
CRC8H
CRC8D

   1             2                1             1           1       u16DataLen + u8OptionLen       1
+------+------------------+---------------+-----------+-----------+-------------/------------+-----------+
| 0x55 |    u16DataLen    |  u8OptionLen  |   u8Type  |   CRC8H   |           DATAS          |   CRC8D   |
+------+------------------+---------------+-----------+-----------+-------------/------------+-----------+

DATAS structure:
                u16DataLen                          u8OptionLen
+--------------------------------------------+----------------------+
|                  Data                      |       Optional       |
+--------------------------------------------+----------------------+
'''

'''
Lookup Table for CRC8 - We'll be using this instead d calculating CRC8 sum
'''
lookupTable_CRC8 = [
  0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15,
  0x38, 0x3f, 0x36, 0x31, 0x24, 0x23, 0x2a, 0x2d,
  0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65,
  0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d,
  0xe0, 0xe7, 0xee, 0xe9, 0xfc, 0xfb, 0xf2, 0xf5,
  0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
  0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85,
  0xa8, 0xaf, 0xa6, 0xa1, 0xb4, 0xb3, 0xba, 0xbd,
  0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2,
  0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea,
  0xb7, 0xb0, 0xb9, 0xbe, 0xab, 0xac, 0xa5, 0xa2,
  0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
  0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32,
  0x1f, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0d, 0x0a,
  0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42,
  0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a,
  0x89, 0x8e, 0x87, 0x80, 0x95, 0x92, 0x9b, 0x9c,
  0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
  0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec,
  0xc1, 0xc6, 0xcf, 0xc8, 0xdd, 0xda, 0xd3, 0xd4,
  0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c,
  0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44,
  0x19, 0x1e, 0x17, 0x10, 0x05, 0x02, 0x0b, 0x0c,
  0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
  0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b,
  0x76, 0x71, 0x78, 0x7f, 0x6A, 0x6d, 0x64, 0x63,
  0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b,
  0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13,
  0xae, 0xa9, 0xa0, 0xa7, 0xb2, 0xb5, 0xbc, 0xbb,
  0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8D, 0x84, 0x83,
  0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb,
  0xe6, 0xe1, 0xe8, 0xef, 0xfa, 0xfd, 0xf4, 0xf3
]

'''
Packet type definitions
'''
ESP_packetTypes = {
    'RESERVED'          : 0x00,
    'RADIO'             : 0x01,
    'RESPONSE'          : 0x02,
    'RADIO_SUB_TEL'     : 0x03,
    'EVENT'             : 0x04,
    'COMMON_COMMAND'    : 0x05,
    'SMART_ACK_COMMAND' : 0x06,
    'REMOTE_MAN_COMMAND': 0x07
}

ESP_COMMON_COMMANDS = {
    'CO_WR_SLEEP'           : {
                        'CMD'       : 0x01,
                        'RESPONSE'  : {
                            # Fields with start byte position, length and field nam
                            
                        }
    },
    'CO_WR_RESET'           : {
                        'CMD'       : 0x02,
                        'RESPONSE'  : {
                        }
    },
    'CO_RD_VERSION'         : {
                        'CMD'       : 0x03,
                        'RESPONSE'  : {
                            'RET_CODE'  : {
                                'NAME'      : 'Return Code',
                                'START'     : 0,
                                'LENGTH'    : 1,
                                'TYPE'      : 'NUMBER'
                            },
                            'APP_VER'   : {
                                'NAME'      : 'Application Version',
                                'START'     : 1,
                                'LENGTH'    : 4,
                                'TYPE'      : 'BYTE_ARRAY'
                            },
                            'API_VER'   : {
                                'NAME'      : 'API Version',
                                'START'     : 5,
                                'LENGTH'    : 4,
                                'TYPE'      : 'BYTE_ARRAY'
                            },
                            'CHIP_ID'   : {
                                'NAME'      : 'Chip ID',
                                'START'     : 9,
                                'LENGTH'    : 4,
                                'TYPE'      : 'NUMBER'
                            },
                            'CHIP_VER'  : {
                                'NAME'      : 'Chip Version',
                                'START'     : 13,
                                'LENGTH'    : 4,
                                'TYPE'      : 'NUMBER'
                            },
                            'APP_DESC'  : {
                                'NAME'      : 'App Description',
                                'START'     : 17,
                                'LENGTH'    : 16,
                                'TYPE'      : 'ASCII'
                            }
                        }
    },
    'C0_RD_SYS_LOG'         : {
                        'CMD'       : 0x04,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_SYS_LOG'         : {
                        'CMD'       : 0x05,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_BIST'            : {
                        'CMD'       : 0x06,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_IDBASE'          : {
                        'CMD'       : 0x07,
                        'RESPONSE'  : {
                        }
    },
    'CO_RD_IDBASE'          : {
                        'CMD'       : 0x08,
                        'RESPONSE'  : {
                            'RET_CODE'  : {
                                'NAME'      : 'Return Code',
                                'START'     : 0,
                                'LENGTH'    : 1,
                                'TYPE'      : 'NUMBER'
                            },
                            'BASE_ID'   : {
                                'NAME'      : 'Base ID',
                                'START'     : 1,
                                'LENGTH'    : 4,
                                'TYPE'      : 'NUMBER'
                            }
                        }
    },
    'CO_WR_REPEATER'        : {
                        'CMD'       : 0x09,
                        'RESPONSE'  : {
                        }
    },
    'CO_RD_REPEATER'        : {
                        'CMD'       : 0x0A,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_FILTER_ADD'      : {
                        'CMD'       : 0x0B,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_FILTER_DEL'      : {
                        'CMD'       : 0x0C,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_FILTER_DEL_ALL'  : {
                        'CMD'       : 0x0D,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_FILTER_ENABLE'   : {
                        'CMD'       : 0x0E,
                        'RESPONSE'  : {
                        }
    },
    'CO_RD_FILTER'          : {
                        'CMD'       : 0x0F,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_WAIT_MATURITY'   : {
                        'CMD'       : 0x10,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_SUBTEL'          : {
                        'CMD'       : 0x11,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_MEM'             : {
                        'CMD'       : 0x12,
                        'RESPONSE'  : {
                        }
    },
    'CO_RD_MEM'             : {
                        'CMD'       : 0x13,
                        'RESPONSE'  : {
                        }
    },
    'CO_RD_MEM_ADDRESS'     : {
                        'CMD'       : 0x14,
                        'RESPONSE'  : {
                        }
    },
    'CO_RD_SECURITY'        : {
                        'CMD'       : 0x15,
                        'RESPONSE'  : {
                        }
    },
    'CO_WR_SECURITY'        : {
                        'CMD'       : 0x22,
                        'RESPONSE'  : {
                        }
    }
}

'''
Function    : ESP_calcCRC8( data )
Description : Calculates CRC8 of data provided
Arguments   : data - list of raw data( ASCII code )
Returns     : calculated CRC8 sum
'''
def ESP_calcCRC8( data ):
    crc8Sum = 0
    for byte in data:
        crc8Sum = lookupTable_CRC8[crc8Sum ^ byte]
    return crc8Sum

'''
Function    : EO_sendData
Description : Acts as the interface to EnOcean gateway device
Arguments   : 2
              hSerial - handle to serial port to which device is connected
              rawData - data to send as list in raw ( number, base:dec ) format
Returns     : stream of raw data received as response, empty list if no response
'''

def EO_sendData( hSerial, rawData ):
    for idx in range( len( rawData ) ):
        hSerial.write( chr(rawData[idx]) )
    time.sleep( 0.010 )
    rawResp = EO_receiveData( hSerial )
    return rawResp

'''
Function    : EO_receiveData
Description : Acts as the read interface to EnOcean gateway device
Arguments   : hSerial - handle to serial port to read from
Returns     : stream of raw data read, empty list if nothing read
'''
def EO_receiveData( hSerial ):
    data = []
    while hSerial.inWaiting() != 0:
        #~ data.append( hSerial.read(1).encode("hex") )
        data.append( ord(hSerial.read(1)) )
        time.sleep( 0.01 )
    return data

'''
Function    : decodePacket
Description : decodes the given raw data packet into fields
Arguments   : rawData
Returns     : a hashtable containing each field by name
                Return hashtable contains these feilds
                    Sync        : UN_IN  (not initialized)
                                  NOT_OK (first byte is not SYNC byte )
                                  OK     ( First byte is SYNC byte )
                    dataLength  : length of data ( 16bits )
                    optDataLen  : optional data length ( 8bits )
                    pktType     : packet type
                    crc8h_recv  : received CRC8H
                    crc8h_calc  : calcualted CRC8H
                    crc8h_stat  : OK - crc8h_recv == crc8h_calc
                                  NOT_OK - otherwise
                    data_recv   : received data as list of ASCII codes
                    opData_recv : received optional data as ASCII codes
                    crc8d_recv  : received CRC8D
                    crc8d_calc  : calculated CRC8D
                    crc8d_stat  : OK - crc8d_recv == crc8d_calc
                                  NOT_OK - otherwise
'''
def ESP_decodePacket( rawData ):
    packetInfo = {}    
    packetInfo[ 'Sync' ] = 'UN_IN'
    
    if( rawData[0] != 0x55 ):
        packetInfo[ 'Sync' ] = 'NOT_OK'
        return packetInfo
    else:
        packetInfo[ 'Sync' ] = 'OK'
    
    # Extract header
    packetInfo[ 'dataLength' ] = rawData[1]*256+rawData[2]
    packetInfo[ 'optDataLen' ] = rawData[3]
    packetInfo[ 'pktType' ]    = rawData[4]
    packetInfo[ 'crc8h_recv' ] = rawData[5]
    packetInfo[ 'crc8h_calc' ] = ESP_calcCRC8( rawData[1:5] )
    if( packetInfo['crc8h_calc'] == packetInfo['crc8h_recv'] ):
        packetInfo['crc8h_stat'] = 'OK'
    else:
        packetInfo['crc8h_stat'] = 'NOT_OK'
        return packetInfo           # Return with partially filled
    
    # Extract data
    packetInfo[ 'data_recv' ]   = rawData[6:6+packetInfo['dataLength']]
    packetInfo[ 'opData_recv' ] = rawData[6+packetInfo['dataLength']:6+packetInfo['dataLength']+packetInfo['optDataLen']]
    packetInfo[ 'crc8d_recv' ]  = rawData[6+packetInfo['dataLength']+packetInfo['optDataLen']]
    packetInfo[ 'crc8d_calc' ]  = ESP_calcCRC8( rawData[ 6:6+packetInfo['dataLength']+packetInfo['optDataLen']] )
    if( packetInfo['crc8d_calc'] == packetInfo['crc8d_recv'] ):
        packetInfo['crc8d_stat'] = 'OK'
    else:
        packetInfo['crc8d_stat'] = 'NOT_OK'

    return packetInfo

'''
Function    : ESP_decodeRadioData
Description : decode each field in data part of a RADIO telegram into a hash table
Arguments   : pktInfo -- decoded Packet info table as generated by ESP_decodePacket
Returns     : none
'''
def ESP_decodeRadioData( pktInfo ):
    print "        [MSG] RADIO packet decoding not implemeted"
    print "        Data : %s " %pktInfo['data_recv']
    print "        Optional Data : %s" %pktInfo['opData_recv']

'''
Function    : ESP_decodeResponseData
Description : decode each field in data part of a RESPONSE telegram into a hash table
Arguments   : pktInfo -- decoded Packet info table as generated by ESP_decodePacket
Returns     : none
'''
def ESP_decodeResponseData( pktInfo, cmd ):
    decodedData = {}
    # variables to hold decoded data
    l_fieldName = "NONE"
    l_fieldValue = 0
    l_fieldStart = 0
    l_fieldEnd = 0
    if cmd in ESP_COMMON_COMMANDS:
        for field in ESP_COMMON_COMMANDS[cmd]['RESPONSE']:            
            l_fieldName = ESP_COMMON_COMMANDS[cmd]['RESPONSE'][field]['NAME']
            l_fieldStart = ESP_COMMON_COMMANDS[cmd]['RESPONSE'][field]['START']
            l_fieldEnd = l_fieldStart + ESP_COMMON_COMMANDS[cmd]['RESPONSE'][field]['LENGTH']
            
            if ESP_COMMON_COMMANDS[cmd]['RESPONSE'][field]['TYPE'] == 'BYTE_ARRAY':
                l_fieldValue = pktInfo['data_recv'][l_fieldStart:l_fieldEnd]
            elif ESP_COMMON_COMMANDS[cmd]['RESPONSE'][field]['TYPE'] == 'NUMBER':
                l_fieldValue = 0;
                for byte in pktInfo['data_recv'][l_fieldStart:l_fieldEnd]:
                    l_fieldValue = l_fieldValue*256 + byte
            elif ESP_COMMON_COMMANDS[cmd]['RESPONSE'][field]['TYPE'] == 'ASCII':
                l_fieldValue = ''.join( chr(i) for i in pktInfo['data_recv'][l_fieldStart:l_fieldEnd] )
            else:
                l_fieldValue = pktInfo['data_recv'][l_fieldStart:l_fieldEnd+1]
            decodedData[l_fieldName] = l_fieldValue
    else:
        print 'ERROR : Command %s not supported' %( cmd )
    
    return decodedData

'''
Function    : displayPacketInfo
Description : displays each field of a packet in formatted form
Arguments   : info -- returned from ESP_decodePacket or approprately framed
Returns     : none
'''
def ESP_displayPacketInfo( pktInfo, cmd = 'NO_CMD' ):
    # Check whether a valid packet
    if( pktInfo['crc8h_stat'] != 'OK' ):
        print 'ERROR : CRC8H mismatch.'
        return
    if( pktInfo['crc8d_stat'] != 'OK' ):
        print 'ERROR : CRC8D mismatch.'
        return
    
    # Display Packet Information
    print '    Header :'
    print '        Data Length          : %4d Bytes' %pktInfo['dataLength']
    print '        Optional Data Length : %4d Bytes' %pktInfo['optDataLen']
    print '        Packet Type          : %s' %(ESP_packetTypes.keys()[ESP_packetTypes.values().index( pktInfo['pktType'] )])
    print '    Data   :'

    if pktInfo['pktType'] == ESP_packetTypes['RESERVED']:
        print "ERROR : RESERVED packet type."
    elif pktInfo['pktType'] == ESP_packetTypes['RADIO']:
        dataFields = ESP_decodeRadioData( pktInfo )
        # @TODO : display each fields
    elif pktInfo['pktType'] == ESP_packetTypes['RESPONSE']:
        dataFields = ESP_decodeResponseData( pktInfo, cmd )
        if dataFields:
            for field in dataFields.keys():
                if( (type(dataFields[field]) == int) or
                   (type(dataFields[field]) == long) ):
                    print "        %-20s : 0x%X" %( field, dataFields[field] )
                else:
                    print "        %-20s : %s" %( field, dataFields[field] )
        else:
            print 'ERROR : Cannot decode data for command %s' %(cmd)
        # @TODO : display each fields
    elif pktInfo['pktType'] == ESP_packetTypes['RADIO_SUB_TEL']:
        print "Unsupported Packet type : RADIO_SUB_TEL"
    elif pktInfo['pktType'] == ESP_packetTypes['EVENT']:
        print "Unsupported Packet type : EVENT"
    elif pktInfo['pktType'] == ESP_packetTypes['COMMON_COMMAND']:
        print "Unsupported Packet type : COMMON_COMMAND"
    elif pktInfo['pktType'] == ESP_packetTypes['SMART_ACK_COMMAND']:
        print "Unsupported Packet type : SMART_ACK_COMMAND"
    elif pktInfo['pktType'] == ESP_packetTypes['REMOTE_MAN_COMMAND']:   # REMOTE_MAN_COMMMAND
        print "Unsupported Packet type : REMOTE_MAN_COMMAND"
    else:
        print "ERROR : Packet type unsupported."
    
    print ''

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
    print "\t\t***********************************************"
    print "\t\t*    Enocean Py - Monitor Enocean devices     *"
    print "\t\t***********************************************"
    ttyPort = "/dev/ttyACM0"
    print "\tUsing serial port : " + ttyPort + '\n'
    
    # CO_RD_VERSION command
    cmd0 = [ 0x55, 0x00, 0x01, 0x00, 0x05, 0x70, 0x03, 0x09 ]
    # CO_RD_IDBASE command
    cmd1 = [ 0x55, 0x00, 0x01, 0x00, 0x05, 0x70, 0x08, 0x38 ]
    
    hEOGateway = serial.Serial( ttyPort, 57600, timeout = 0 )
    
    ## Send CO_RD_VERSION
    print "RQST       : ",
    for i in range( len( cmd0 ) ):
        print "%02X" %( cmd0[i] ),
    print ''
    EO_receiveData( hEOGateway )        # Read any buffered data
    rawResp = EO_sendData( hEOGateway, cmd0 )
    print 'RESP(%3dB) : ' %len( rawResp ),
    for i in range( len( rawResp ) ):
        print "%02X" %(rawResp[i]),
    print ''
    pkt = ESP_decodePacket( rawResp )
    ESP_displayPacketInfo( pkt, 'CO_RD_VERSION' )
    
    ## Send CO_RD_IDBASE
    print "RQST       : ",
    for i in range( len( cmd1 ) ):
        print "%02X" %( cmd1[i] ),
    print ''
    #~ EO_receiveData( hEOGateway )        # Read any buffered data
    rawResp = EO_sendData( hEOGateway, cmd1 )
    print 'RESP(%3dB) : ' %len( rawResp ),
    for i in range( len( rawResp ) ):
        print "%02X" %(rawResp[i]),
    print ''
    pkt = ESP_decodePacket( rawResp )
    ESP_displayPacketInfo( pkt, 'CO_RD_IDBASE' )
    
    try:
        while( True ):
            rawResp = EO_receiveData( hEOGateway )
            if rawResp:
                print 'RECEIVED :',
                for i in range( len( rawResp ) ):
                    print "%02X" %(rawResp[i]),
                print ''
                pkt = ESP_decodePacket( rawResp )
                ESP_displayPacketInfo( pkt )
    except:
        print "\nExiting Enocean Py"
        hEOGateway.close()
        print "Bye..bye.. :) "
    
if __name__ == "__main__":
    main()
