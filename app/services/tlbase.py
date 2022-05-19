#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/tlbase.py
#
#   TLBase is base class used by teamleader services ContactService and CompanyService
#   TODO: move some more common code here later
#

from viaa.configuration import ConfigParser


class TLBase:
    def read_custom_labels(self):
        # read teamleader field labels from configmap
        config = ConfigParser()
        self.labels = config.app_cfg['custom_field_labels']
