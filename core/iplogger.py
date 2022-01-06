from dataclasses import dataclass
from functools import wraps
import datetime

from core.exceptions import BadRequestError

from flask import request

""" Log ips so we can decide if we're being DDOSed """

@dataclass
class IP():
    ip: str
    dt: datetime.datetime = None

    def __post_init__(self):
        self.dt = datetime.datetime.utcnow()

    def is_too_soon(self, seconds):
        """ Check if last call from ip is within x seconds from now """
        return (datetime.datetime.utcnow() - self.dt) < datetime.timedelta(seconds=seconds)


class IPLogger():
    def __init__(self):
        self._ip_log = []

    def add_ip(self, ip):
        self._ip_log.append(IP(ip))

    def check_ip(self, ip, seconds):
        try:
            log_ip = next(iter(reversed([x for x in self._ip_log if x.ip == ip])))
        except StopIteration:
            return True

        return not log_ip.is_too_soon(seconds)

    def check_ddos(self, func):
        """ Wrapper function to check if ip is not DDOSing us """
        @wraps(func)
        def inside(*args, **kwargs):
            ip_address = request.remote_addr

            if not self.check_ip(ip_address, 20):
                self.add_ip(ip_address)
                raise BadRequestError("To soon")

            self.add_ip(ip_address)
            return func(*args, **kwargs)

        return inside
