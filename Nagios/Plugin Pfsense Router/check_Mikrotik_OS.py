#!/usr/bin/env python3


import argparse
import sys
import datetime
import urllib.request
import ssl
from packaging.version import Version, parse

#MIKROTIK-MIB::
#MIKROTIK-MIB::mtxrLicVersion.0
OID_RouterOSVersion = '.1.3.6.1.4.1.14988.1.1.4.4.0'  # Current RouterOS version on device
#MIKROTIK-MIB::mtxrFirmwareVersion.0
OID_CurrentFirmwareVersion = '.1.3.6.1.4.1.14988.1.1.7.4.0'  # Current RouterOS Firmware Version on device
#MIKROTIK-MIB::mtxrFirmwareUpgradeVersion.0
OID_LatestFirmwareVersion = '.1.3.6.1.4.1.14988.1.1.7.7.0'  # Latest availble RouterOS Firmware Version

baseURLS = {"https://download.mikrotik.com/", "https://upgrade.mikrotik.com/" }
debug = False;

def nagios_exit(overallStatus, message):

    #print(overallStatus + " : " + message)
    print(overallStatus, ":", message)

    if overallStatus == "Ok":
        sys.exit(0)
    if overallStatus == "Warning":
        sys.exit(1)
    if overallStatus == "Critical":
        sys.exit(2)
    if overallStatus == "Unknown":
        sys.exit(3)

try:
    from pysnmp.hlapi import *

except:
    message = """This script requires the followng non standard libaries to run:
    * pysnmp
"""
    nagios_exit("Unknown", message)


def getLatestMikrotik(ReleaseChannel):

    error = ""

    for EachBaseURL in baseURLS:

        # Get the lasest Version number from the Mikrotik website based on the
        # supplied release channel.

        # Define URLS.  (Note that only RouterOS V6 is currently supported.
        currentURL = "routeros/LATEST.6"
        bugFixOnlyURL = "routeros/LATEST.6fix"
        RCURL = "routeros/LATEST.6rc"

        if ReleaseChannel == "Current":
            URL = EachBaseURL + currentURL
        elif ReleaseChannel == "Bugfix":
            URL = EachBaseURL + bugFixOnlyURL
        elif ReleaseChannel == "ReleaseCandidate":
            URL = EachBaseURL + RCURL
        else:
            nagios_exit("Unknown", "Unknown Mikrotik Release Channel")

        try:

            with urllib.request.urlopen(URL) as response:
                ReturnedString = response.read()

            ReturnedString = ReturnedString.decode('utf-8')
            ReturnedString = ReturnedString.split()
            lastestVersion = ReturnedString[0]
            ReleaseDate = ReturnedString[1]
            return lastestVersion, ReleaseDate
        except ssl.CertificateError as e:
            debugMessage(URL)
            error =  e
            debugMessage(e)

        except Exception as e:
            debugMessage(e.__class__)
            debugMessage(e)
            nagios_exit("Unknown", "Could not retrive latest RouterOS version from Mikrotik Website")

    nagios_exit("Unknown", "Could not retrive latest RouterOS version from Mikrotik Website:" + str(error))

def debugMessage(message):
    if debug == True:
        print ("debug: " + str(message))

def getSNMP_OID(IPAddress, Version, SNMPOptions, OID):

    # Gets the SNMP OID from the requested OID.

    if Version == "2c":
        g = getCmd(SnmpEngine(),
                   CommunityData(SNMPOptions['Community']),
                   UdpTransportTarget((IPAddress, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(OID))
                   )

    errorIndication, errorStatus, errorIndex, varBinds = next(g)
    if errorIndication is None:
        firstrow = varBinds[0]  # note that any subsequent results are discarded
        return firstrow[1]
    else:
        nagios_exit("Unknown", "SNMP Communication Error")


def process_cli():

    parser = argparse.ArgumentParser()

    parser.add_argument('-H', '--hostIP',
                         help='Mikrotik Router IP Address',
                         type=str, required=True)
    parser.add_argument('-v', '--snmpVersion',
                         help='SNMP Version (only 2c currently supported) ',
                         type=str, required=True)
    parser.add_argument('-C', '--snmpCommunity',
                         help='SNMP Community String (only v1 and 2c) ', type=str, required=False)
    parser.add_argument('-c', '--mikrotikReleaseChannel',
                         help='The mikrotik release channel to check for updates against: Bugfix, Current or \
                         ReleaseCandidate',
                         type=str, required=True)

    # Parse arguments and die if error
    try:
        args = parser.parse_args()
    except Exception:
        sys.exit(3)

    if not args.snmpCommunity and args.snmpVersion != 3:
        print ("SNMP Community string required for SNMP Versions other than v3.")
        sys.exit(3)

    return args


def OutOfDate(CurrentVersionString, LatestVersionString):

    try:
        CurrentVersionString = str(CurrentVersionString)
        CurrentVersionString = CurrentVersionString.replace('rc', 'b')
        CurrentVersion = Version(str(CurrentVersionString))

    except:
        message = "Don't know how to handle current version number"
        nagios_exit('Unknown', message)

    try:
        # if the length of the string is 0 then it can't be a proper version number.
        if len(LatestVersionString) == 0:
             raise
        LatestVersionString = str(LatestVersionString)
        LatestVersionString = LatestVersionString.replace('rc', 'b')
        LatestVersion = Version(LatestVersionString)
    except:
        message = "Don't know how to handle latest number"
        nagios_exit('Unknown', message)

    if LatestVersion > CurrentVersion:
        return True
    else:
        return False

def statusCheck(currentStatus, NewStatus):

    # Function to take two Nagios status and return the worst case.

    if currentStatus == 'Critical' or NewStatus == 'Critical':
        return 'Critical'
    elif currentStatus == 'Warning' or NewStatus == 'Warning':
        return 'Warning'
    elif  currentStatus == 'Unknown' or NewStatus == 'Unknown':
        return 'Unknown'
    else:
        return 'Ok'


def main():

    args = process_cli()
    SNMPOptions = {'Community': args.snmpCommunity}

    # Get information from SNMP and mikrotik websites about version mumbers
    LatestRouterOSVersion, LatestRouterOSVersion_ReleaseDate = (getLatestMikrotik(args.mikrotikReleaseChannel))
    CurrentRouterOsVerion = str((getSNMP_OID(args.hostIP, args.snmpVersion, SNMPOptions, OID_RouterOSVersion)))

    #them code o day
    print("Current RouterOS Version:", CurrentRouterOsVerion)

    CurrentFirmwareVersion = getSNMP_OID(args.hostIP, args.snmpVersion, SNMPOptions, OID_CurrentFirmwareVersion)
    LastestFirmwareVersion = getSNMP_OID(args.hostIP, args.snmpVersion, SNMPOptions, OID_LatestFirmwareVersion)

    # Determine RouterOS Version Status
    if OutOfDate(CurrentRouterOsVerion, LatestRouterOSVersion) is False:
        RouterOSMessage = "RouterOS is up to date (" + CurrentRouterOsVerion + ")."
        RouterOSStatus = 'Ok'
    else:
        now = datetime.datetime.now()
        dateofLastRelease = datetime.datetime.fromtimestamp(float(LatestRouterOSVersion_ReleaseDate))
        delta = now - dateofLastRelease
        RouterOSMessage = "Router upgrade from " + CurrentRouterOsVerion + " to " + LatestRouterOSVersion + " is required"
        if delta.days < 7:
            RouterOSStatus = 'Warning'
        else:
            RouterOSStatus = 'Critical'

    # Determine current Firmware Status

    if OutOfDate(CurrentFirmwareVersion, LastestFirmwareVersion):
        firmwareMessage = "Firmware Requires Upgrade (" + CurrentFirmwareVersion + " -> " + LastestFirmwareVersion + ")."
        firmwareStatus = "Critical"
    else:
        firmwareMessage = "Firmware is up to date (" + CurrentFirmwareVersion + ")."
        firmwareStatus = "Ok"

    # Figure out overall status

    overallStatus = statusCheck(RouterOSStatus, firmwareStatus)

    if overallStatus == "Ok":
        message = "RouterOS and Firmware is up to date" + " (" + CurrentRouterOsVerion + "/" \
                   + CurrentFirmwareVersion + ")."
        nagios_exit("OK", message)
    else:
        nagios_exit(overallStatus, RouterOSMessage + " " + firmwareMessage)


if __name__ == "__main__":
    main()

