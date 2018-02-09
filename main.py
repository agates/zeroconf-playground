#!/usr/bin/env python3

import signal
import socket
import sys

import re
from capnpy.struct_ import Struct
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from zeroconf import ServiceInfo, Zeroconf

from schema.ph_event import PhEvent
from schema.struct_handler_info import StructHandlerInfo


def get_primary_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # open any connection, even if its unreachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except socket._socket.gaierror:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def underscore_to_camelcase(s):
    return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), s)


class DataPathwayProtocol(DatagramProtocol):
    def __init__(self, capnproto_struct, handlers):
        self.capnproto_struct = capnproto_struct
        self.handlers = handlers

    def datagramReceived(self, datagram, addr):
        if datagram:
            for handler in self.handlers:
                try:
                    handler(self.capnproto_struct.loads(datagram), addr)
                except EOFError as e:
                    print(e)


class Announcer:
    def __init__(self,
                 zeroconf_sub_type="capnproto",
                 zeroconf_type="_data-pathway._udp.local.",
                 zeroconf_service_address=get_primary_ip(),
                 zeroconf_server="{0}.local.".format(socket.gethostname())):
        self.zeroconf_sub_type = zeroconf_sub_type
        self.zeroconf_type = zeroconf_type
        self.zeroconf_service_address = zeroconf_service_address
        self.zeroconf_server = zeroconf_server

        self.zeroconf_info = None
        self.zeroconf = Zeroconf()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.zeroconf_info:
            self.zeroconf.unregister_service(self.zeroconf_info)
        self.zeroconf.close()

    def register_pathway(self, capnproto_struct, handlers):
        if not issubclass(capnproto_struct, Struct):
            raise ValueError("capnproto_struct must be a capnpy Struct")

        if len(handlers) == 0:
            raise ValueError("Must specify at least one handler")

        for handler in handlers:
            if not callable(handler):
                raise ValueError("Handler must be callable")

        handlers = tuple(handlers)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind(('', 0))
        port = sock.getsockname()[1]

        reactor.adoptDatagramPort(
            sock.fileno(), socket.AF_INET,
            DataPathwayProtocol(capnproto_struct, handlers)
        )
        sock.close()

        data_pathway = StructHandlerInfo(
            struct_name=capnproto_struct.__name__,
            handlers=[underscore_to_camelcase(handler.__name__) for handler in handlers]
        )

        self.zeroconf_info = ServiceInfo(
            self.zeroconf_type,
            "{0}._sub.{1}".format(
                self.zeroconf_sub_type,
                self.zeroconf_type
            ),
            socket.inet_aton(self.zeroconf_service_address),
            port,
            0, 0,
            {b"struct-handler-info": data_pathway.dumps()},
            self.zeroconf_server
        )

        self.zeroconf.register_service(self.zeroconf_info, allow_name_change=True)


def log_phevent(datagram, addr):
    print("Message[{0}:{1}] - ph={2}, timestamp={3}".format(
        str(addr[0]), str(addr[1]), str(datagram.ph), str(datagram.timestamp)
    ))


def do_something_else_with_phevent(datagram, addr):
    print("Passing")
    pass


signal.signal(signal.SIGINT, signal.default_int_handler)

with Announcer() as announcer:
    announcer.register_pathway(
        PhEvent, [
            log_phevent,
            do_something_else_with_phevent
        ]
    )

    try:
        reactor.run()
    except KeyboardInterrupt:
        pass
    finally:
        sys.exit()
