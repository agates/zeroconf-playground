#!/usr/bin/env python3

import socket

from zeroconf import ServiceInfo, Zeroconf

from schema.ph_event import PhEvent


def get_primary_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # open any connection, even if its unreachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


class Announcer:
    def __init__(self,
                 zeroconf_service_name="data-pathway",
                 zeroconf_type="_capnproto._udp.local.",
                 zeroconf_service_address=get_primary_ip(),
                 zeroconf_server="{0}.local.".format(socket.gethostname())):
        self.zeroconf_service_name = zeroconf_service_name
        self.zeroconf_type = zeroconf_type
        self.zeroconf_service_address = zeroconf_service_address
        self.zeroconf_server = zeroconf_server

        self.info = None
        self.sock = None
        self.capnproto_type = None
        self.handler = None

        self.zeroconf = Zeroconf()

    def __del__(self):
        if self.info:
            self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()
        if self.sock:
            self.sock.close()

    def register_pathway(self, capnproto_type, handler):
        self.capnproto_type = capnproto_type
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.info = ServiceInfo(self.zeroconf_type,
                                "{0}.{1}".format(
                                    self.zeroconf_service_name, self.zeroconf_type
                                ),
                                socket.inet_aton(self.zeroconf_service_address),
                                self.sock.getsockname()[1],
                                0, 0,
                                {"type": self.capnproto_type.__name__},
                                self.zeroconf_server)
        self.handler = handler
        self.zeroconf.register_service(self.info)

    def run_loop(self):
        # TODO: Replace this with a thread (or just migrate to something like twisted)

        while True:
            # TODO: Explore buffer sizes
            r = self.sock.recvfrom(1024)

            if not r[0]:
                continue

            try:
                self.handler(self.capnproto_type.loads(r[0]), r[1])
            except EOFError as e:
                print(e)


announcer = Announcer()
announcer.register_pathway(PhEvent,
                           lambda data, addr:
                           print("Message[{0}:{1}] - ph={2}, timestamp={3}".format(
                               str(addr[0]), str(addr[1]), str(data.ph), str(data.timestamp)))
                           )
try:
    announcer.run_loop()
except KeyboardInterrupt:
    pass
