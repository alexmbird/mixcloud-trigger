#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import sys
from clint.textui import puts, puts_err, indent, colored


class Metadata(dict):
    
    """Simple JSON Metadata persistence; backed to a file full of JSON"""
    
    def __init__(self, filename, defaults, verbose=False):
        super(Metadata,self).__init__()
        self.filename = filename
        self.defaults = defaults
        self.verbose  = verbose
        self.load()
    
    
    def save(self):
        """Persist metadata for this source"""
        with open(self.filename, 'w') as f:
            json.dump(self, f)
        if self.verbose:
            puts("Saved metadata to %s" % (self.filename,))

    
    def load(self):
        """Restore metadata for this source"""
        try:
            with open(self.filename, 'r') as f:
                for k, v in json.load(f).items():
                    self[k] = v
            if self.verbose:
                puts("Loaded metadata from %s" % (self.filename,))
        except FileNotFoundError:
            for k, v in self.defaults.items():
                self[k] = v
            self.save()
            if self.verbose:
                puts("Created new metadata %s" % self.filename)
