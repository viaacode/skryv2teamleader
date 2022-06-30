#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/mock_slack_wrapper.py
#
#     Mocks slack message calls on the SlackWrapper. This way we don't send real messages
#     but still test most logic in SlackClient itself
#

from tests.unit.mock_client import MockClient


class MockSlackWrapper(MockClient):
    def __init__(self):
        super().__init__()

    def create_message(self, message):
        super().method_call(
            f"create_message: message={message}"
        )

    def chat_postMessage(self, channel, text):
        super().method_call(
            f"chat_postMessage: {channel} {text}"
        )
