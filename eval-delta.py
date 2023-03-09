#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from collections import OrderedDict
from optparse import OptionParser, OptionGroup
import gcmstoolbox


usage = "usage: %prog JSON"
  
parser = OptionParser(usage)

(options, args) = parser.parse_args()


if len(args) != 1:
    print("no single argument given, exiting...\n")
    exit()

in_file = args[0]
data = gcmstoolbox.openJSON(in_file)
groups = data["groups"]

for key, value in groups.items():
    if value["deltaRI"] > 1:
        print(f"{key}\t{value['deltaRI']}")

