#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# MixCloud API docs @ https://www.mixcloud.com/developers/

import requests
import time
from dateutil.parser import parse as du_parse
import pprint
import sys
import subprocess, shlex, tempfile
import os, os.path, glob
import configparser


from cli_parser import cliparser
from metadata import Metadata


class MixCloudItem(object):
    
    """A single, processable Cloudcast"""
    
    # self.xx properties passed in action commands
    ACTION_VARS = ['type', 'name', 'url', 'created_time']

    def __init__(self, t, name, url, created_time):
        super(MixCloudItem, self).__init__()
        self.type           = t
        self.name           = name
        self.url            = url
        self.created_time   = du_parse(created_time)
    
    def __str__(self):
        return "<%s (%s) - '%s' @ %s>" % (self.__class__.__name__, self.type, self.name, self.created_time)
    
    
    def _escaped_shell_vars(self):
        """Return dict of ACTION_VARS but escaped for passing to shell cmd"""
        return {k:shlex.quote(str(getattr(self,k))) for k in self.ACTION_VARS}
    
    
    def shell_action(self, action):
        """Run a shell command, interpolating (with escapes) vars for this item"""
        format_args = self._escaped_shell_vars()
        cmd = action.format(**format_args)
        # Why all this tempfile nonsense?  Becuase subprocess and `sh -c`
        # cannot be trusted to pass args as real args.  Best to run the action
        # as a script.
        with tempfile.NamedTemporaryFile() as script:
            script.write(bytes(cmd, 'utf8'))
            script.flush()
            with open(script.name, 'r') as f:
                print("  Will exec: %s" % f.read())
            cp = subprocess.run(
                ['/bin/sh', script.name],
                check=True,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT
            )
        print("  Output: %s" % cp.stdout)



class MixCloudSource(object):
    
    """Represent a MixCloud feed/channel."""
    
    # Metadata handling
    METADATA_SUBDIR     = "mixcloud"
    DEFAULT_METADATA    = {
        'last_scrape': 0
    }
    
    def __init__(self, gconf, source_name, source_conf):
        super(MixCloudSource, self).__init__()
        self.global_conf    = gconf
        self.source_name    = source_name
        self.source_conf    = source_conf
        self.metadata       = Metadata(
            self._metadata_path_name(), 
            self.DEFAULT_METADATA )
        self.n_yielded      = 0

    
    def __enter__(self):
        self.metadata.load()
        return self

    
    def __exit__(self, type, value, traceback):
        self.metadata.save()
    
    
    def _get_data(self, *args):
        raise NotImplementedError("Subclass me")
    
    
    def _item_to_mcis(self, data):
        """Yield MCI(s) from a feed item."""
        t = data['type']
        for cc in data['cloudcasts']:
            try:
                yield MixCloudItem(
                    t, 
                    cc['name'], 
                    cc['url'], cc['created_time']
                )
            except KeyError as e:
                print(e)
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(cc)
                raise
    
    # Lookup table for the kinds of feed item we can handle.  Presently 
    # _item_to_mcis supports all but can add others.
    TYPE_MAP = {
        'upload':       _item_to_mcis,
        'favorite':     _item_to_mcis,
        # 'favorite':     _favourite_to_mcis
    }


    
    def get_new_items(self, want_types=None, force_all=False):
        """Return any new items we found"""
        wt = self.source_conf.get('want_types', 'upload,favorite').split(',')
        j = self._get_data()
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(self.metadata)
        
        n_yielded = 0
        max_items = self.source_conf.getint('max_items', None)
        
        for obj in j['data']:
            t = obj['type']
            if t in wt:
                funk = self.TYPE_MAP.get(t, None)
                if funk:
                    for mci in funk(self, obj):
                        ctime_epoch = float( mci.created_time.strftime("%s") )
                        if force_all or ctime_epoch > self.metadata['last_scrape']:
                            yield mci
                            n_yielded += 1
                            if max_items:
                                if not force_all:
                                    if n_yielded >= max_items:
                                        print("Reached max_items of %d for %s" % (max_items, self.source_name))
                                        break
                            
                else:
                    print("Don't know how to handle requested type '%s'" % t, file=sys.stderr)
                    # pp = pprint.PrettyPrinter(indent=4)
                    # pp.pprint(obj)
                    # sys.exit(0)
        
        self.metadata['last_scrape'] = time.time()

    
    def _metadata_path_name(self):
        """Figure out where to keep this source's Metadata"""
        my_metadata_dir = os.path.join(
            self.global_conf['metadata']['metadata_path'],
            self.METADATA_SUBDIR
        )
        if not os.path.isdir(my_metadata_dir):
            os.mkdir(my_metadata_dir)
        return os.path.join(my_metadata_dir, self.source_name+'.json')


        

class MixCloudSourceFeed(MixCloudSource):
    
    def _get_data(self):
        r = requests.get('https://api.mixcloud.com/%s/feed/' % self.source_name)
        j = r.json()
        return j


if __name__ == "__main__":
    args = cliparser.parse_args()
    
    # Read global config
    gconf = configparser.ConfigParser()
    gconf.read(args.conf)
    
    # Read per-source config
    src_glob = os.path.join(gconf['sources']['sources_dir'], '*.conf')
    print("Loading sources from %s" % src_glob)
    for f in glob.glob(src_glob):
        print("Reading per-source conf %s" % f)
        sconf = configparser.ConfigParser()
        sconf.read(f)
        for source_name in sconf.sections():
            this_src_conf = sconf[source_name]
            with MixCloudSourceFeed(gconf, source_name, this_src_conf) as s:
                items = s.get_new_items(force_all=args.all)
                for i in items:
                    print("%s" % i)
                    if 'item_action' in this_src_conf:
                        i.shell_action(this_src_conf['item_action'])

