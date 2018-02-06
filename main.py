#!/usr/bin/env python3

import socket

from zeroconf import ServiceInfo, Zeroconf

from schema.ph_event import PhEvent

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
zeroconf = Zeroconf()

try:
    sock.bind(('0.0.0.0', 5500))
    info = ServiceInfo("_capnproto._udp.local.",
                       "data-listener._capnproto._udp.local.",
                       socket.inet_aton('192.168.1.46'), 5500, 0, 0,
                       {"type": "PhEvent"}, "tempest.local.")
    zeroconf.register_service(info)
    while True:
        # receive data from client (data, addr)
        d = sock.recvfrom(1024)
        data = d[0]
        addr = d[1]

        if not data:
            continue

        ph_event = PhEvent.loads(data)

        print("Message[{0}:{1}] - ph={2}, timestamp={3}".format(
            str(addr[0]), str(addr[1]), str(ph_event.ph), str(ph_event.timestamp))
        )
except KeyboardInterrupt:
    pass
finally:
    zeroconf.unregister_all_services()
    zeroconf.close()
    sock.close()

