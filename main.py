#!/usr/bin/env python3

import re
import signal
import socket
import sys

from capnpy.struct_ import Struct
import psycopg2cffi.extras
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from zeroconf import ServiceInfo, Zeroconf

from schema.ph_event import PhEvent
from schema.struct_handler_info import StructHandlerInfo
from settings import *


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
            struct_name=bytes(capnproto_struct.__name__, 'UTF-8'),
            handlers=[bytes(underscore_to_camelcase(handler.__name__), 'UTF-8') for handler in handlers]
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
    print("Message[{0}:{1}] - group_name={2}, ph={3}, timestamp={4}".format(
        str(addr[0]), str(addr[1]),
        datagram.group_name.decode("UTF-8"), datagram.ph.decode("UTF-8"), str(datagram.timestamp)
    ))


def insert_into_database(datagram, addr):
    insert_query = '''INSERT INTO public.phlogs(
                        ph, logtime, group_name)
                        VALUES (%s, to_timestamp(%s), %s)'''
    cursor.execute(insert_query,
                   (datagram.ph.decode("UTF-8"),
                    datagram.timestamp / 10 ** 9,
                    datagram.group_name.decode("UTF-8"))
                   )
    connection.commit()


signal.signal(signal.SIGINT, signal.default_int_handler)

with Announcer() as announcer:
    with psycopg2cffi.connect(database=database, user=user, password=password, host=host, port=port) as connection:
        with connection.cursor(cursor_factory=psycopg2cffi.extras.DictCursor) as cursor:
            announcer.register_pathway(
                PhEvent, [
                    log_phevent,
                    insert_into_database
                ]
            )

            try:
                reactor.run()
            except KeyboardInterrupt:
                pass
            finally:
                sys.exit()
