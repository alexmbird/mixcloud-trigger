#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest
import tempfile
import os.path

from mctdb import MixCloudSeenDB


class TestMixCloudSeenDB(unittest.TestCase):


    def setUp(self):
        self.mdata_tempdir = tempfile.TemporaryDirectory('mct_meta_temp')
        self.db_num = 0  # counter for filenames
        # print("Made metadata tempdir %s" % self.mdata_tempdir.name)


    def tearDown(self):
        self.mdata_tempdir.cleanup()


    def _genDBPath(self, name='testdb'):
        self.db_num += 1
        filename = name + '_' + str(self.db_num) + '.db'
        return os.path.join(self.mdata_tempdir.name, filename)

    
    def _makeDb(self, name='testdb'):
        p = self._genDBPath(name)
        return MixCloudSeenDB(p)

        
    def testCreateEmpty(self):
        "Create a new metadata obj from scratch"
        p = self._genDBPath()
        self.assertFalse(os.path.isfile(p))
        db1 = MixCloudSeenDB(p)
        self.assertTrue(os.path.isfile(p)) # gets created
        db1.close()
        del db1
        self.assertTrue(os.path.isfile(p))


    def testIsProcessedAbsent(self):
        "Absent feed item has not been processed"
        db1 = self._makeDb()
        self.assertFalse(db1.is_processed('dfgsfg'))
    
    
    def testIsProcessedAdd(self):
        "Absent feed item has not been processed"
        p = self._genDBPath(name='consistentfilename')
        db1 = MixCloudSeenDB(p)
        self.assertFalse(db1.is_processed('dfgsfg'))
        self.assertFalse(db1.is_processed('asasdas'))
        db1.add_processed('dfgsfg')
        self.assertTrue(db1.is_processed('dfgsfg'))
        self.assertFalse(db1.is_processed('asasdas'))
        db1.close()
        del db1
        db2 = MixCloudSeenDB(p)
        self.assertTrue(db2.is_processed('dfgsfg'))
        self.assertFalse(db2.is_processed('asasdas'))
    
    
    def testInsertDuplicate(self):
        "Can't insert a duplicate key"
        p = self._genDBPath(name='consistentfilename')
        db1 = MixCloudSeenDB(p)
        self.assertFalse(db1.is_processed('dfgsfg'))
        db1.add_processed('dfgsfg')
        self.assertTrue(db1.is_processed('dfgsfg'))
        with self.assertRaises(KeyError):
            db1.add_processed('dfgsfg')
