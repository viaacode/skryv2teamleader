#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/mock_client.py
#
#     Used by teamleader_client and other clients to keep track
#     of methods called and arguments passed to mocked method calls
#

class MockClient:
    def __init__(self):
        self.calls = []

    def method_called(self, name):
        for m in self.calls:
            if name in m:
                return True

        return False

    def method_call_args_match(self, method_name, args_array):
        for m in self.calls:
            if method_name in m:
                for arg in args_array:
                    if arg not in m:
                        return False
                return True

        return False

    def method_call(self, method_and_args):
        self.calls.append(method_and_args)

    def all_method_calls(self):
        return self.calls

    def last_method_called(self):
        return self.calls[-1]
