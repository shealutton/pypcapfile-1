#!/usr/bin/env python
"""
This is the test case for the savefile.
"""

import os
import pickle
import tempfile
import unittest
import base64

import pcapfile.test.fixture as fixture
from pcapfile import savefile

def create_pcap():
    """Create a capture file from the test fixtures."""
    tfile = tempfile.NamedTemporaryFile()
    try: # python3
        Y = fixture.TESTPCAP3
        X = base64.b64decode(Y)
        capture = pickle.loads(X)
    except ValueError: # python2 unsupported pickle protocol: 3
        Y = fixture.TESTPCAP2
        X = Y.decode('base64')
        capture = pickle.loads(X)
    open(tfile.name, 'wb').write(capture)
    return tfile

class TestCase(unittest.TestCase):
    """
    Test case for the savefile code.
    """
    capfile = None

    def init_capfile(self, layers=0):
        """Initialise the capture file."""
        tfile = create_pcap()
        self.capfile = savefile.load_savefile(tfile, layers=layers)
        tfile.close()
        if os.path.exists(tfile.name):
            os.unlink(tfile.name)

    @classmethod
    def setUpClass(cls):
        """
        Print an intro to identify this test suite when running multiple tests.
        """
        print('[+] loading basic tests')

    def setUp(self):
        """
        Set up a default capture file.
        """
        # only need to initialise capfile on the first time, while being able
        # load it with additional decoding layers.
        if not self.capfile:
            self.init_capfile()

    def test_network_load(self):
        """
        Test that the code that loads network layer packets from the
        top level works.
        """
        self.init_capfile(layers=2)
        for packet in self.capfile.packets:
            for field in ['src', 'dst', 'v', 'hl', 'tos', 'ttl']:
                ipkt = packet.packet.payload
                self.assertTrue(hasattr(ipkt, field), 'invalid packet!')

    def test_frame_load(self):
        """
        Ensure that ethernet frames load from the top level.
        """
        self.init_capfile(layers=1)
        for packet in self.capfile.packets:
            for field in ['src', 'dst', 'type', 'payload']:
                self.assertTrue(hasattr(packet.packet, field),
                                'invalid frame!')

    def test_packet_valid(self):
        """
        Make sure raw packets load properly.
        """
        packet = self.capfile.packets[0].raw()
        if isinstance(packet[14], int): # python3
            expected = 69
        else:# python2
            expected = b'\x45'
        self.assertEqual(packet[14], expected, 'invalid packet')

        for packet in self.capfile.packets:
            for field in ['capture_len', 'timestamp', 'timestamp_ms',
                          'packet', 'header', 'packet_len']:
                self.assertTrue(hasattr(packet, field), 'invalid packet!')

    def test_header_valid(self):
        """
        Test to ensure the header validation code works.
        """
        header = self.capfile.header
        self.assertEqual(header.major, 2, 'invalid major version!')
        self.assertEqual(header.minor, 4, 'invalid minor version!')

    def test_basic_import(self):
        """
        Validate basic parameters of a simple savefile load.
        """
        self.assertTrue(self.capfile.valid, 'invalid capture file')
        self.assertEqual(len(self.capfile.packets), 23,
                         'wrong number of packets!')
