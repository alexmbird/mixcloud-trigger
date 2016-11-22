#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import sys


class Metadata(dict):
    
    """Simple JSON Metadata persistence"""
    
    def __init__(self, filename, defaults):
        super(Metadata,self).__init__()
        self.filename = filename
        self.defaults = defaults
    
    
    def save(self):
        """Persist metadata for this source"""
        with open(self.filename, 'w') as f:
            json.dump(self, f)
        print("Saved metadata to %s" % (self.filename,))

    
    def load(self):
        """Restore metadata for this source"""
        try:
            with open(self.filename, 'r') as f:
                for k, v in json.load(f).items():
                    self[k] = v
            print("Loaded metadata from %s" % (self.filename,))
        except FileNotFoundError:
            for k, v in self.defaults.items():
                self[k] = v
            self.save()
            print("Created new metadata %s" % self.filename, file=sys.stderr)
