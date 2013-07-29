import sys, httplib
import xml.etree.ElementTree as ET

def launchilab(username):

    #from scorm or other format provided by the ServiceBroker 

    # ServuiceBroker Info
    host= "ludi.mit.edu"
    url = "/iLabServiceBroker/iLabServiceBroker.asmx"
    sbGuid = "ISB-247A4591CA1443485D85657CF357"

    # Client specific Info
    groupName = "Experiment_Group"

    # WebLab Micro-electronics -- Batch Applet lab
    webLabClientGuid = "6BD4E985-4967-4742-854B-D44B8B844A21"
    webLabCouponID = "36" 
    webLabPassCode = "EDFCA4AE-A611-48D6-85E3-E86A2728B90A"

    # Time of day without scheduling -- Interactive redirect
    todNotScheduledGuid="2D1888C0-7F43-46DC-AD51-3A77A8DE8152"
    todCouponID = "64"
    todPassCode = "1A20F154-D467-4058-8CF3-CB0E1580F04C"

    #Specific to LMS or other SerrviceBroker registered authority
    authorityGuid = "fakeGUIDforRMLStest-12345"


    #########

    duration = "-1"

    couponID = todCouponID
    passkey = todPassCode
    clientGuid = todNotScheduledGuid

    soapXml = '''<?xml version="1.0" encoding="utf-8"?>
            <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                <soap12:Header>
                    <OperationAuthHeader xmlns="http://ilab.mit.edu/iLabs/type">
                        <coupon  xmlns="http://ilab.mit.edu/iLabs/type">
                            <couponId>''' + couponID + '''</couponId>
                            <issuerGuid>''' + sbGuid + '''</issuerGuid>
                            <passkey>''' + passkey +'''</passkey>
                        </coupon>
                    </OperationAuthHeader>
                </soap12:Header>
                <soap12:Body>
                    <LaunchLabClient xmlns="http://ilab.mit.edu/iLabs/Services">
                        <clientGuid>''' + clientGuid +'''</clientGuid>
                        <groupName>''' + groupName + '''</groupName>
                        <userName>''' + username +'''</userName>
                        <authorityKey>''' + authorityGuid + '''</authorityKey>
                        <duration>''' + duration + '''</duration>
                        <autoStart>1</autoStart>
                    </LaunchLabClient>
                </soap12:Body>
            </soap12:Envelope>'''

    #make connection
    ws = httplib.HTTP(host)
    ws.putrequest("POST", url)

    #add headers
    ws.putheader("Content-Type", "application/soap+xml; charset=utf-8")
    ws.putheader("Content-Length", "%d"%(len(soapXml),))
    ws.endheaders()

    #send request
    ws.send(soapXml)

    #get response
    statuscode, statusmessage, header = ws.getreply()
    #print "Response: ", statuscode, statusmessage
    #print "headers: ", header
    res = ws.getfile().read()
    #print res, "\n"
    root = ET.fromstring(res)
    tag = root[0][0][0][1].text
    return tag
