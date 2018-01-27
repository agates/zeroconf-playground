#!/usr/bin/env python3

import pprint

import ipaddress
from zeroconf import ServiceBrowser, Zeroconf, ZeroconfServiceTypes


class MyListener:

    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Service {0} added".format(name))
        pprint.pprint(info)
        print("\tAddress: {0}".format(ipaddress.IPv4Address(info.address)))
        print()


'''
_googlecast._tcp.local.
_googlezone._tcp.local.
_sftp-ssh._tcp.local.
_ssh._tcp.local.
'''

zeroconf = Zeroconf()
listener = MyListener()
browser1 = ServiceBrowser(zeroconf, "_googlecast._tcp.local.", listener)
browser2 = ServiceBrowser(zeroconf, "_googlezone._tcp.local.", listener)
browser3 = ServiceBrowser(zeroconf, "_sftp-ssh._tcp.local.", listener)
browser4 = ServiceBrowser(zeroconf, "_ssh._tcp.local.", listener)

print('\n'.join(ZeroconfServiceTypes.find()))

try:
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()
