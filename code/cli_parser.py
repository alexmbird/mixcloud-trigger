#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse

cliparser = argparse.ArgumentParser(
    # prog="mixcloud-trigger",
    description='Run local actions when new items are added to MixCloud'
)
cliparser.add_argument('--conf', '-c', type=str, default='conf/main.conf',
                       help='config dir')
cliparser.add_argument('--source', '-s', type=str,
                       help='ignore contents of sources_dir and use single src')
cliparser.add_argument('--all', '-A', const=True, action='store_const', default=False,
                       help='process ALL items, not just new ones')
cliparser.add_argument('--verbose', '-v', const=True, action='store_const', default=False,
                       help='be more verbose')


if __name__ == '__main__':
    args = cliparser.parse_args()
    print("%s" % args)
