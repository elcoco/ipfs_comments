import uuid
from dataclasses import dataclass
import random
from functools import wraps
import logging
import datetime

from core.exceptions import BadRequestError
from core import config

from flask import request

logger = logging.getLogger('app')

""" TODO: auto remove old challenges so we don't have to keep the in memory forever """



class Challenge():
    """ Represents the captcha challenge that is requested by the client. """

    def __init__(self):
        self.uuid: str = uuid.uuid1().hex
        self.challenge, self.solution = self.generate_challenge()
        self.dt = datetime.datetime.utcnow()

    def generate_challenge(self):
        """ Generate a simple calculation """

        words = {
            1 : "one",
            2 : "two",
            3 : "three",
            4 : "four",
            5 : "five",
            6 : "six",
            7 : "seven",
            8 : "eight",
            9 : "nine",
            0 : "zero" }

        a = random.randint(0,9)
        b = random.randint(0,9)

        if ["+", "-"][random.randint(0,1)] == '+':
            solution = a + b
            challenge = f"{words[a]} plus {words[b]}"
        else:
            solution = a - b
            challenge = f"{words[a]} minus {words[b]}"
        return challenge, solution

    def is_expired(self, ttl):
        """ Check if the ttl expired """
        return (datetime.datetime.utcnow() - self.dt).total_seconds() > ttl

    def validate(self, solution):
        return str(solution) == str(self.solution)


class Captcha():
    """ Handles challenges and cleans them up when TTL expired """
    def __init__(self, ttl=300):
        self._ttl = ttl
        self._captchas = []

    def clean_up(self):
        """ Check captchas TTL """
        t_now = datetime.datetime.utcnow()
        for c in self._captchas:
            if c.is_expired(self._ttl):
                self._captchas.remove(c)

    def get_challenge(self):
        c = Challenge()
        self._captchas.append(c)
        return c

    def validate(self, uuid, solution):
        """ Check if captcha is valid, and remove from list """
        # clean up expired captcha's
        self.clean_up()

        try:
            c = next(iter([x for x in self._captchas if x.uuid == uuid]))
            if c.validate(solution):
                self._captchas.remove(c)
                return True
        except StopIteration:
            return False

    def require_captcha(self, func):
        """ Wrapper function that checks for captcha challenge """
        @wraps(func)
        def inside(*args, **kwargs):
            try:
                if not self.validate(request.json["captchaId"],
                                     request.json["captchaSolution"]):
                    logger.error("Failed captcha")
                    raise BadRequestError("Failed captcha check")
            except KeyError:
                logger.error("Missing captcha data")
                raise BadRequestError("Missing captcha data")

            return func(*args, **kwargs)
        return inside
