#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# MixCloud API docs @ https://www.mixcloud.com/developers/

import requests
import time
import datetime
from dateutil.parser import parse as du_parse
import pprint
import sys
import subprocess, shlex, tempfile
import os, os.path, glob
import configparser
from clint.textui import puts, puts_err, indent, colored
import filelock


from cli_parser import cliparser
from mctdb import MixCloudSeenDB



PRINTABLE_DATETIME_FORMAT = "%c"



class MixCloudItem(object):
    
    """A single, processable Cloudcast"""
    
    # self.xx properties passed in action commands
    ACTION_VARS = ['type', 'name', 'url', 'created_time']

    def __init__(self, t, k, name, url, created_time):
        super(MixCloudItem, self).__init__()
        self.type           = t
        self.key            = k
        self.name           = name
        self.url            = url
        self.created_time   = du_parse(created_time)
    
    def __str__(self):
        return "<%s (%s) - '%s' @ %s; key=%s>" % (self.__class__.__name__, self.type, self.name, self.created_time, self.key)
    
    
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
                puts("Will exec: %s" % f.read())
            with indent(2):
                # Not available until Python 3.5
                # cp = subprocess.run(
                #     ['/bin/sh', script.name],
                #     check=True,
                #     stdout=subprocess.PIPE, 
                #     stderr=subprocess.STDOUT
                # )
                
                try:
                    output = subprocess.check_output(
                        ['/bin/sh', script.name],
                        stderr=subprocess.STDOUT
                    )
                except subprocess.CalledProcessError as e:
                    puts_err(colored.red("Action returned error code %d" % e.returncode))
                    puts_err(e.output)
                    raise
                else:
                    puts("Output: %s" % output)



class MixCloudSource(object):
    
    """Represent a MixCloud feed/channel."""
    
    # Metadata handling
    METADATA_SUBDIR     = "mixcloud"
    
    def __init__(self, gconf, source_name, source_conf, verbose=False):
        super(MixCloudSource, self).__init__()
        self.global_conf    = gconf
        self.source_name    = source_name
        self.source_conf    = source_conf
        self.verbose        = verbose
        self.metadata_db    = MixCloudSeenDB(
            self._metadata_db_name(),
            verbose=self.verbose
        )
        self.n_yielded      = 0

    
    def __enter__(self):
        # self.metadata.load()  # implicit now
        return self

    
    def __exit__(self, type, value, traceback):
        pass
    
    
    def _get_data(self, *args):
        raise NotImplementedError("Subclass me")
    
    
    def _item_to_mcis(self, data):
        """Yield MCI(s) from a feed item."""
        t = data['type']
        for cc in data['cloudcasts']:
            try:
                yield MixCloudItem(
                    t,
                    cc['key'],
                    cc['name'], 
                    cc['url'], cc['created_time']
                )
            except KeyError as e:
                puts_err(colored.red(e))
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


    def get_unprocessed_items(self, want_types=None, force_all=False):
        """Return new items we found"""
        wt = self.source_conf.get('want_types', 'upload,favorite').split(',')
        j = self._get_data()
        
        n_items     = 0
        max_items   = self.source_conf.getint('max_items', None)
        
        for obj in j['data']:
            t = obj['type']
            if t in wt:
                # pp = pprint.PrettyPrinter(indent=4)
                # pp.pprint(obj)
                funk = self.TYPE_MAP.get(t, None)
                if funk:
                    for mci in funk(self, obj):
                        ctime_epoch = float( mci.created_time.strftime("%s") )
                        if force_all or not self.metadata_db.is_processed(mci.key):
                            if n_items < max_items or max_items is None:
                                yield mci
                                n_items += 1  # Counting feed items, not cc's
                            else:
                                puts(colored.red("Ignored (> max_items): %s" % mci))
                        else:
                            if self.verbose:
                                puts(colored.red("Already processed: %s" % mci))
                    if max_items:
                        if not force_all:
                            if n_items == max_items:
                                puts(colored.magenta("Reached max_items of %d for %s" % (max_items, self.source_name)))
                            
                else:
                    puts_err(colored.red("Don't know how to handle requested type '%s'" % t))
                    # pp = pprint.PrettyPrinter(indent=4)
                    # pp.pprint(obj)
                    # sys.exit(0)

    
    def _metadata_db_name(self):
        """Figure out where to keep this source's Metadata"""
        my_metadata_dir = os.path.join(
            self.global_conf['metadata']['metadata_path'],
            self.METADATA_SUBDIR
        )
        if not os.path.isdir(my_metadata_dir):
            os.makedirs(my_metadata_dir)
        return os.path.join(my_metadata_dir, self.source_name+'.db')


        

class MixCloudSourceFeed(MixCloudSource):
    
    def _get_data(self):
        r = requests.get('https://api.mixcloud.com/%s/feed/' % self.source_name)
        j = r.json()
        return j






if __name__ == "__main__":
    args = cliparser.parse_args()
    
    # Read global config
    try:
        if args.verbose:
            puts("Reading config from %s" % args.conf)
        with open(args.conf, 'r') as f:
            gconf = configparser.ConfigParser()
            gconf.read_file(f)
    except FileNotFoundError:
        puts_err(colored.red("Error: cannot read main config file '%s'" % args.conf))
        sys.exit(1)
    
    # Only one instance should be running at once.  Do file-based locking.
    lock_path = os.path.join(gconf['metadata']['metadata_path'], 'mixcloud-trigger.lock')
    lock = filelock.FileLock(lock_path)
    try:
        lock.acquire(timeout=5)
    except  filelock.Timeout as e:
        puts_err(colored.red(str(e)))
        sys.exit(0)
    
    # Read per-source config
    if gconf['sources']['sources_dir'].startswith('/'):
        sources_dir = gconf['sources']['sources_dir']
    else:
        sources_dir = os.path.join(
            os.path.dirname(args.conf),
            gconf['sources']['sources_dir']
        )
    src_glob = os.path.join(sources_dir, '*.conf')
    if args.verbose:
        puts("Loading sources from %s" % src_glob)
    for f in glob.glob(src_glob):
        puts("Handling per-source conf %s" % f)
        with indent(2):
            sconf = configparser.ConfigParser()
            sconf.read(f)
            for source_name in sconf.sections():
                this_src_conf = sconf[source_name]
                with MixCloudSourceFeed(gconf, source_name, this_src_conf, verbose=args.verbose) as s:
                    items = s.get_unprocessed_items(force_all=args.all)
                    for i in items:
                        puts(colored.green("%s" % i))
                        with indent(2):
                            try:
                                if 'item_action' in this_src_conf:
                                    i.shell_action(this_src_conf['item_action'])
                            except subprocess.CalledProcessError as e:
                                pass
                            else:
                                # Mark as processed - but only if successful
                                s.metadata_db.add_processed(i.key)
