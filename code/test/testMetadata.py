#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest
import tempfile
import os.path

from metadata import Metadata


class TestMetadata(unittest.TestCase):

    
    def setUp(self):
        self.mdata_tempdir = tempfile.TemporaryDirectory('mct_meta_temp')
        # print("Made metadata tempdir %s" % self.mdata_tempdir.name)

    
    def tearDown(self):
        self.mdata_tempdir.cleanup()
    
    def _genMDPath(self, name='abcde'):
        return os.path.join(self.mdata_tempdir.name, name + '.json')
    

    def testCreateEmpty(self):
        "Create a new metadata obj from scratch"
        p = self._genMDPath()
        self.assertFalse(os.path.isfile(p))
        md1 = Metadata(p, {})
        self.assertTrue(os.path.isfile(p)) # gets created
        md1.save()
        del md1
        self.assertTrue(os.path.isfile(p))
            
    
    def testStoreKey(self):
        "Store & retrieve a key with save"
        p = self._genMDPath()
        md1 = Metadata(p, {})
        md1['mykey'] = 'abcd'
        md1.save()
        del md1
        md2 = Metadata(p, {})
        self.assertEqual(md2['mykey'], 'abcd')


    def testNoStoreWithoutSave(self):
        "Store & retrieve fails without save"
        p = self._genMDPath()
        md1 = Metadata(p, {})
        md1['mykey'] = 'abcd'
        # md1.save()
        del md1
        md2 = Metadata(p, {})
        with self.assertRaises(KeyError):
            a = md2['mykey']
