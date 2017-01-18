#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sqlite3
from clint.textui import puts, puts_err, indent, colored


class MixCloudSeenDB(object):
    
    """Maintain a simple database of the items we've already processed for a
    given source.  This came about because of an apparent delay between the real
    upload and MC's created_time caused items to fall beneath the simple
    last_scrape_time threshold and be lost. """
    
    # Limitations: bit rough & ready; not suitable for multithreading?
    
    SQL_CREATE = """
CREATE TABLE IF NOT EXISTS items_processed(
    item_key TEXT,
    ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_key)
)
    """.strip()
    
    
    def __init__(self, filename, verbose=False):
        super(MixCloudSeenDB,self).__init__()
        self.verbose = verbose
        if self.verbose:
            puts("Using DB at %s" % filename)
        self.conn = sqlite3.connect(filename)
        self.conn.execute(self.SQL_CREATE)
    
    
    def __del__(self):
        self.close()
    
    
    def close(self):
        try:
            self.conn.commit()
            self.conn.close()
        except sqlite3.ProgrammingError as e:
            pass
            
    
    def add_processed(self, item_key):
        """Note an item as processed"""
        cur = self.conn.cursor()
        if self.verbose:
            puts("DB: setting '%s' seen" % (item_key,))
        try:
            cur.execute("INSERT INTO items_processed(item_key) VALUES(?)", (item_key,))
        except sqlite3.IntegrityError:
            raise KeyError("Processed item already exists")
        self.conn.commit()
        
        
    def is_processed(self, item_key):
        """Check if a feed identified by item_key has been successfully
        processed"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM items_processed WHERE item_key=?", (item_key,))
        r = cur.fetchone()
        return r[0] > 0
    