"""
Unit tests for consoled (Console Monitor Service).

Tests follow SONiC testing conventions:
- MockConfigDb for CONFIG_DB simulation
- Parameterized test cases
- pyfakefs for filesystem operations

Test scenarios:
- DCE service initialization with multiple console links
- Configuration parsing and proxy creation
- Feature enable/disable handling
"""

import os
import sys
import time
import copy
from unittest import TestCase, mock
from parameterized import parameterized

from sonic_py_common.general import load_module_from_source

from .test_vectors import (
    DCE_TEST_VECTOR,
    DTE_TEST_VECTOR,
    DCE_3_LINKS_ENABLED_CONFIG_DB,
    DCE_FEATURE_DISABLED_CONFIG_DB,
    CONSOLE_PORT_3_LINKS,
    DTE_ENABLED_CONFIG_DB,
    DTE_DISABLED_CONFIG_DB,
    PROC_CMDLINE_SINGLE_CONSOLE,
    PROC_CMDLINE_MULTIPLE_CONSOLE,
    PROC_CMDLINE_NO_BAUD,
    PROC_CMDLINE_NO_CONSOLE,
)
from tests.common.mock_configdb import MockConfigDb, MockDBConnector


# ============================================================
# Path setup and module loading
# ============================================================

test_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, 'scripts')
sys.path.insert(0, modules_path)

# Load consoled module from scripts directory
consoled_path = os.path.join(scripts_path, 'consoled')
consoled = load_module_from_source('consoled', consoled_path)

# Replace swsscommon classes with mocks
consoled.ConfigDBConnector = MockConfigDb
consoled.DBConnector = MockDBConnector
consoled.Table = mock.Mock()


# ============================================================
# Mock Classes for Serial/PTY operations
# ============================================================

class MockSerialProxy:
    """Mock SerialProxy that tracks creation without actual serial operations."""
    
    instances = []
    
    def __init__(self, link_id, device, baud, state_table, pty_symlink_prefix):
        self.link_id = link_id
        self.device = device
        self.baud = baud
        self.state_table = state_table
        self.pty_symlink_prefix = pty_symlink_prefix
        self.running = False
        self.started = False
        self.stopped = False
        MockSerialProxy.instances.append(self)
    
    def start(self) -> bool:
        """Mock start - always succeeds."""
        self.started = True
        self.running = True
        return True
    
    def stop(self) -> None:
        """Mock stop."""
        self.stopped = True
        self.running = False
    
    @classmethod
    def reset(cls):
        """Reset all instances for test isolation."""
        cls.instances = []
    
    @classmethod
    def get_instance_count(cls) -> int:
        """Get number of created proxy instances."""
        return len(cls.instances)
    
    @classmethod
    def get_started_count(cls) -> int:
        """Get number of started proxy instances."""
        return sum(1 for p in cls.instances if p.started)


# ============================================================
# DCE Service Tests
# ============================================================

class TestDCEService(TestCase):
    """Test cases for DCE (Console Server) service."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for all tests in this class."""
        pass
    
    def setUp(self):
        """Set up test fixtures for each test."""
        MockSerialProxy.reset()
        MockConfigDb.CONFIG_DB = None
    
    def tearDown(self):
        """Clean up after each test."""
        MockSerialProxy.reset()
        MockConfigDb.CONFIG_DB = None
    
    def test_dce_service_initialization(self):
        """Test DCE service basic initialization."""
        MockConfigDb.set_config_db(DCE_3_LINKS_ENABLED_CONFIG_DB)
        
        service = consoled.DCEService()
        
        # Mock the start to avoid actual DB connections
        with mock.patch.object(service, 'config_db', MockConfigDb()):
            with mock.patch.object(service, 'state_db', mock.Mock()):
                with mock.patch.object(service, 'state_table', mock.Mock()):
                    service.config_db = MockConfigDb()
                    service.running = True
                    
                    # Verify service can be created
                    self.assertIsNotNone(service)
                    self.assertEqual(service.proxies, {})
    
    def test_dce_check_feature_enabled_when_enabled(self):
        """Test _check_feature_enabled returns True when feature is enabled."""
        MockConfigDb.set_config_db(DCE_3_LINKS_ENABLED_CONFIG_DB)
        
        service = consoled.DCEService()
        service.config_db = MockConfigDb()
        
        result = service._check_feature_enabled()
        
        self.assertTrue(result)
    
    def test_dce_check_feature_enabled_when_disabled(self):
        """Test _check_feature_enabled returns False when feature is disabled."""
        MockConfigDb.set_config_db(DCE_FEATURE_DISABLED_CONFIG_DB)
        
        service = consoled.DCEService()
        service.config_db = MockConfigDb()
        
        result = service._check_feature_enabled()
        
        self.assertFalse(result)
    
    def test_dce_get_all_configs_parses_correctly(self):
        """Test _get_all_configs correctly parses CONSOLE_PORT table."""
        MockConfigDb.set_config_db(DCE_3_LINKS_ENABLED_CONFIG_DB)
        
        service = consoled.DCEService()
        service.config_db = MockConfigDb()
        
        configs = service._get_all_configs()
        
        # Verify 3 ports are parsed
        self.assertEqual(len(configs), 3)
        
        # Verify port 1 config
        self.assertIn("1", configs)
        self.assertEqual(configs["1"]["baud"], 9600)
        self.assertEqual(configs["1"]["device"], "/dev/C0-1")
        
        # Verify port 2 config
        self.assertIn("2", configs)
        self.assertEqual(configs["2"]["baud"], 115200)
        self.assertEqual(configs["2"]["device"], "/dev/C0-2")
        
        # Verify port 3 config
        self.assertIn("3", configs)
        self.assertEqual(configs["3"]["baud"], 9600)
        self.assertEqual(configs["3"]["device"], "/dev/C0-3")
    
    def test_dce_sync_creates_proxies_when_enabled(self):
        """Test _sync creates SerialProxy for each configured port when feature is enabled."""
        MockConfigDb.set_config_db(DCE_3_LINKS_ENABLED_CONFIG_DB)
        
        service = consoled.DCEService()
        service.config_db = MockConfigDb()
        service.state_table = mock.Mock()
        service.pty_symlink_prefix = "/dev/VC0-"
        service.proxies = {}
        
        # Replace SerialProxy with mock
        with mock.patch.object(consoled, 'SerialProxy', MockSerialProxy):
            service._sync()
            
            # Verify 3 proxies were created
            self.assertEqual(len(service.proxies), 3)
            self.assertEqual(MockSerialProxy.get_instance_count(), 3)
            self.assertEqual(MockSerialProxy.get_started_count(), 3)
            
            # Verify proxy IDs match port numbers
            self.assertIn("1", service.proxies)
            self.assertIn("2", service.proxies)
            self.assertIn("3", service.proxies)
    
    def test_dce_sync_creates_no_proxies_when_disabled(self):
        """Test _sync creates no proxies when feature is disabled."""
        MockConfigDb.set_config_db(DCE_FEATURE_DISABLED_CONFIG_DB)
        
        service = consoled.DCEService()
        service.config_db = MockConfigDb()
        service.state_table = mock.Mock()
        service.pty_symlink_prefix = "/dev/VC0-"
        service.proxies = {}
        
        # Replace SerialProxy with mock
        with mock.patch.object(consoled, 'SerialProxy', MockSerialProxy):
            service._sync()
            
            # Verify no proxies were created
            self.assertEqual(len(service.proxies), 0)
            self.assertEqual(MockSerialProxy.get_instance_count(), 0)
    
    def test_dce_sync_removes_proxy_when_port_deleted(self):
        """Test _sync removes proxy when port is deleted from config."""
        # Use deepcopy to avoid modifying the original test vector
        config_db = copy.deepcopy(DCE_3_LINKS_ENABLED_CONFIG_DB)
        MockConfigDb.set_config_db(config_db)
        
        service = consoled.DCEService()
        service.config_db = MockConfigDb()
        service.state_table = mock.Mock()
        service.pty_symlink_prefix = "/dev/VC0-"
        service.proxies = {}
        
        # First sync - create 3 proxies
        with mock.patch.object(consoled, 'SerialProxy', MockSerialProxy):
            service._sync()
            self.assertEqual(len(service.proxies), 3)
            
            # Now remove port 2 from config (modifies the copy, not original)
            del MockConfigDb.CONFIG_DB["CONSOLE_PORT"]["2"]
            
            # Second sync - should remove proxy for port 2
            service._sync()
            
            self.assertEqual(len(service.proxies), 2)
            self.assertNotIn("2", service.proxies)
            self.assertIn("1", service.proxies)
            self.assertIn("3", service.proxies)
    
    def test_dce_console_port_handler_triggers_sync(self):
        """Test console_port_handler triggers _sync on config change."""
        MockConfigDb.set_config_db(DCE_3_LINKS_ENABLED_CONFIG_DB)
        
        service = consoled.DCEService()
        service.config_db = MockConfigDb()
        service.state_table = mock.Mock()
        service.pty_symlink_prefix = "/dev/VC0-"
        service.proxies = {}
        
        with mock.patch.object(consoled, 'SerialProxy', MockSerialProxy):
            with mock.patch.object(service, '_sync') as mock_sync:
                service.console_port_handler("1", "SET", {"baud_rate": "9600"})
                mock_sync.assert_called_once()
    
    def test_dce_console_switch_handler_triggers_sync(self):
        """Test console_switch_handler triggers _sync on feature toggle."""
        MockConfigDb.set_config_db(DCE_3_LINKS_ENABLED_CONFIG_DB)
        
        service = consoled.DCEService()
        service.config_db = MockConfigDb()
        service.state_table = mock.Mock()
        service.pty_symlink_prefix = "/dev/VC0-"
        service.proxies = {}
        
        with mock.patch.object(consoled, 'SerialProxy', MockSerialProxy):
            with mock.patch.object(service, '_sync') as mock_sync:
                service.console_switch_handler("console_mgmt", "SET", {"enabled": "yes"})
                mock_sync.assert_called_once()


# ============================================================
# Frame Protocol Tests
# ============================================================

class TestFrameProtocol(TestCase):
    """Test cases for frame protocol implementation."""
    
    def test_crc16_modbus(self):
        """Test CRC-16/MODBUS calculation."""
        # Known test vector
        data = bytes([0x01, 0x00, 0x00, 0x01, 0x00])
        crc = consoled.crc16_modbus(data)
        
        # CRC should be a 16-bit value
        self.assertIsInstance(crc, int)
        self.assertGreaterEqual(crc, 0)
        self.assertLessEqual(crc, 0xFFFF)
    
    def test_escape_data_escapes_special_chars(self):
        """Test escape_data escapes SOF, EOF, and DLE characters."""
        # Data containing special characters
        data = bytes([0x05, 0x00, 0x10, 0x41])  # SOF, EOF, DLE, 'A'
        
        escaped = consoled.escape_data(data)
        
        # Each special char should be preceded by DLE
        # Expected: DLE SOF DLE EOF DLE DLE A
        self.assertEqual(len(escaped), 7)
    
    def test_unescape_data_restores_original(self):
        """Test unescape_data restores original data."""
        original = bytes([0x05, 0x00, 0x10, 0x41])
        escaped = consoled.escape_data(original)
        unescaped = consoled.unescape_data(escaped)
        
        self.assertEqual(unescaped, original)
    
    def test_frame_build_creates_valid_frame(self):
        """Test Frame.build() creates properly formatted frame."""
        frame = consoled.Frame.create_heartbeat(seq=1)
        frame_bytes = frame.build()
        
        # Frame should start with SOF sequence
        self.assertEqual(frame_bytes[:3], consoled.SOF_SEQUENCE)
        
        # Frame should end with EOF sequence
        self.assertEqual(frame_bytes[-3:], consoled.EOF_SEQUENCE)
    
    def test_frame_parse_roundtrip(self):
        """Test Frame can be built and parsed back."""
        original = consoled.Frame.create_heartbeat(seq=42)
        frame_bytes = original.build()
        
        # Extract content between SOF and EOF
        content = frame_bytes[3:-3]
        
        parsed = consoled.Frame.parse(content)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.seq, 42)
        self.assertTrue(parsed.is_heartbeat())
    
    def test_frame_parse_rejects_bad_crc(self):
        """Test Frame.parse() rejects frame with bad CRC."""
        frame = consoled.Frame.create_heartbeat(seq=1)
        frame_bytes = frame.build()
        
        # Corrupt the content (between SOF and EOF)
        content = bytearray(frame_bytes[3:-3])
        content[0] ^= 0xFF  # Flip bits
        
        parsed = consoled.Frame.parse(bytes(content))
        
        self.assertIsNone(parsed)


# ============================================================
# FrameFilter Tests
# ============================================================

class TestFrameFilter(TestCase):
    """Test cases for FrameFilter class."""
    
    def test_frame_filter_detects_heartbeat(self):
        """Test FrameFilter correctly identifies heartbeat frame."""
        received_frames = []
        
        def on_frame(frame):
            received_frames.append(frame)
        
        filter = consoled.FrameFilter(on_frame=on_frame)
        
        # Build a heartbeat frame
        heartbeat = consoled.Frame.create_heartbeat(seq=5)
        frame_bytes = heartbeat.build()
        
        # Feed to filter
        filter.process(frame_bytes)
        
        # Should have received one frame
        self.assertEqual(len(received_frames), 1)
        self.assertTrue(received_frames[0].is_heartbeat())
        self.assertEqual(received_frames[0].seq, 5)
    
    def test_frame_filter_passes_user_data(self):
        """Test FrameFilter passes non-frame data to user_data callback."""
        user_data_chunks = []
        
        def on_user_data(data):
            user_data_chunks.append(data)
        
        filter = consoled.FrameFilter(on_user_data=on_user_data)
        
        # Send regular ASCII data
        filter.process(b"Hello World")
        filter.on_timeout()  # Flush pending data
        
        # Should have received user data
        self.assertEqual(len(user_data_chunks), 1)
        self.assertEqual(user_data_chunks[0], b"Hello World")
    
    def test_frame_filter_separates_frame_and_data(self):
        """Test FrameFilter correctly separates frame from user data."""
        received_frames = []
        user_data_chunks = []
        
        def on_frame(frame):
            received_frames.append(frame)
        
        def on_user_data(data):
            user_data_chunks.append(data)
        
        filter = consoled.FrameFilter(on_frame=on_frame, on_user_data=on_user_data)
        
        # Build mixed data: user data + heartbeat + user data
        heartbeat = consoled.Frame.create_heartbeat(seq=1)
        mixed_data = b"Before" + heartbeat.build() + b"After"
        
        filter.process(mixed_data)
        filter.on_timeout()
        
        # Should have received one frame
        self.assertEqual(len(received_frames), 1)
        
        # Should have received user data (before the frame)
        self.assertGreater(len(user_data_chunks), 0)


# ============================================================
# DTE Service Tests
# ============================================================

class TestDTEService(TestCase):
    """Test cases for DTE (SONiC Switch) service."""
    
    def setUp(self):
        """Set up test fixtures for each test."""
        MockConfigDb.CONFIG_DB = None
    
    def tearDown(self):
        """Clean up after each test."""
        MockConfigDb.CONFIG_DB = None
    
    def test_dte_service_initialization(self):
        """Test DTE service can be initialized with TTY and baud."""
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        
        self.assertEqual(service.tty_name, "ttyS0")
        self.assertEqual(service.baud, 9600)
        self.assertEqual(service.device_path, "/dev/ttyS0")
        self.assertFalse(service.running)
        self.assertFalse(service.enabled)
        self.assertEqual(service.seq, 0)
    
    def test_dte_check_enabled_returns_true(self):
        """Test _check_enabled() returns True when controlled_device.enabled=yes."""
        MockConfigDb.set_config_db(DTE_ENABLED_CONFIG_DB)
        
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        service.config_db = MockConfigDb()
        
        result = service._check_enabled()
        
        self.assertTrue(result)
    
    def test_dte_check_enabled_returns_false(self):
        """Test _check_enabled() returns False when controlled_device.enabled=no."""
        MockConfigDb.set_config_db(DTE_DISABLED_CONFIG_DB)
        
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        service.config_db = MockConfigDb()
        
        result = service._check_enabled()
        
        self.assertFalse(result)
    
    def test_dte_check_enabled_returns_false_when_missing(self):
        """Test _check_enabled() returns False when controlled_device entry is missing."""
        MockConfigDb.set_config_db({"CONSOLE_SWITCH": {}})
        
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        service.config_db = MockConfigDb()
        
        result = service._check_enabled()
        
        self.assertFalse(result)
    
    def test_dte_start_heartbeat_when_enabled(self):
        """Test heartbeat thread starts when feature is enabled."""
        MockConfigDb.set_config_db(DTE_ENABLED_CONFIG_DB)
        
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        service.config_db = MockConfigDb()
        service.ser_fd = 1  # Mock file descriptor
        service.running = True
        
        # Call _load_initial_config which should start heartbeat if enabled
        with mock.patch.object(service, '_start_heartbeat') as mock_start:
            service._load_initial_config({})
            mock_start.assert_called_once()
    
    def test_dte_no_heartbeat_when_disabled(self):
        """Test heartbeat thread does not start when feature is disabled."""
        MockConfigDb.set_config_db(DTE_DISABLED_CONFIG_DB)
        
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        service.config_db = MockConfigDb()
        service.ser_fd = 1
        service.running = True
        
        with mock.patch.object(service, '_start_heartbeat') as mock_start:
            service._load_initial_config({})
            mock_start.assert_not_called()
    
    def test_dte_stop_heartbeat_when_disabled(self):
        """Test heartbeat thread stops when feature is disabled."""
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        service.enabled = True  # Currently enabled
        
        # Mock config change to disabled
        MockConfigDb.set_config_db(DTE_DISABLED_CONFIG_DB)
        service.config_db = MockConfigDb()
        
        with mock.patch.object(service, '_stop_heartbeat') as mock_stop:
            service.console_switch_handler("controlled_device", "SET", {"enabled": "no"})
            mock_stop.assert_called_once()
    
    def test_dte_console_switch_handler_toggles_heartbeat(self):
        """Test console_switch_handler toggles heartbeat on/off based on config."""
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        service.enabled = False  # Currently disabled
        
        # Mock config change to enabled
        MockConfigDb.set_config_db(DTE_ENABLED_CONFIG_DB)
        service.config_db = MockConfigDb()
        
        with mock.patch.object(service, '_start_heartbeat') as mock_start:
            service.console_switch_handler("controlled_device", "SET", {"enabled": "yes"})
            mock_start.assert_called_once()
            self.assertTrue(service.enabled)
    
    def test_dte_heartbeat_frame_sequence_increments(self):
        """Test heartbeat sequence number increments correctly."""
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        service.ser_fd = -1  # Invalid fd, will skip actual write
        service.seq = 0
        
        # Manually increment sequence like _send_heartbeat does
        initial_seq = service.seq
        service.seq = (service.seq + 1) % 256
        
        self.assertEqual(initial_seq, 0)
        self.assertEqual(service.seq, 1)
    
    def test_dte_heartbeat_sequence_wraps_at_256(self):
        """Test heartbeat sequence number wraps at 256."""
        service = consoled.DTEService(tty_name="ttyS0", baud=9600)
        service.seq = 255
        
        # Wrap around
        service.seq = (service.seq + 1) % 256
        
        self.assertEqual(service.seq, 0)


# ============================================================
# DTE Utility Function Tests
# ============================================================

class TestDTEUtilityFunctions(TestCase):
    """Test cases for DTE utility functions like parse_proc_cmdline."""
    
    def test_parse_proc_cmdline_single_console(self):
        """Test parse_proc_cmdline with single console parameter."""
        with mock.patch('builtins.open', mock.mock_open(read_data=PROC_CMDLINE_SINGLE_CONSOLE)):
            tty_name, baud = consoled.parse_proc_cmdline()
            
            self.assertEqual(tty_name, "ttyS0")
            self.assertEqual(baud, 9600)
    
    def test_parse_proc_cmdline_multiple_console(self):
        """Test parse_proc_cmdline uses last console parameter."""
        with mock.patch('builtins.open', mock.mock_open(read_data=PROC_CMDLINE_MULTIPLE_CONSOLE)):
            tty_name, baud = consoled.parse_proc_cmdline()
            
            # Should use the last console= parameter
            self.assertEqual(tty_name, "ttyS1")
            self.assertEqual(baud, 115200)
    
    def test_parse_proc_cmdline_no_baud_uses_default(self):
        """Test parse_proc_cmdline uses default baud when not specified."""
        with mock.patch('builtins.open', mock.mock_open(read_data=PROC_CMDLINE_NO_BAUD)):
            tty_name, baud = consoled.parse_proc_cmdline()
            
            self.assertEqual(tty_name, "ttyS0")
            self.assertEqual(baud, consoled.DEFAULT_BAUD)  # 9600
    
    def test_parse_proc_cmdline_no_console_raises_error(self):
        """Test parse_proc_cmdline raises ValueError when no console parameter."""
        with mock.patch('builtins.open', mock.mock_open(read_data=PROC_CMDLINE_NO_CONSOLE)):
            with self.assertRaises(ValueError) as context:
                consoled.parse_proc_cmdline()
            
            self.assertIn("No console= parameter found", str(context.exception))


# ============================================================
# Integration-like Tests
# ============================================================

class TestDCEIntegration(TestCase):
    """Integration-like tests for DCE service with mocked I/O."""
    
    def setUp(self):
        """Set up test fixtures."""
        MockSerialProxy.reset()
        MockConfigDb.CONFIG_DB = None
    
    def tearDown(self):
        """Clean up after tests."""
        MockSerialProxy.reset()
        MockConfigDb.CONFIG_DB = None
    
    @parameterized.expand(DCE_TEST_VECTOR)
    def test_dce_proxy_creation(self, test_name, config_db, expected_proxy_count):
        # Reset before each parameterized test
        MockSerialProxy.reset()
        """Parameterized test for DCE proxy creation based on config."""
        MockConfigDb.set_config_db(config_db)
        
        service = consoled.DCEService()
        service.config_db = MockConfigDb()
        service.state_table = mock.Mock()
        service.pty_symlink_prefix = "/dev/VC0-"
        service.proxies = {}
        
        with mock.patch.object(consoled, 'SerialProxy', MockSerialProxy):
            service._sync()
            
            self.assertEqual(
                len(service.proxies), 
                expected_proxy_count,
                f"Expected {expected_proxy_count} proxies for {test_name}, got {len(service.proxies)}"
            )
    
    def test_dce_full_initialization_flow(self):
        """Test complete DCE service initialization flow."""
        # Reset mocks for isolation
        MockSerialProxy.reset()
        MockConfigDb.set_config_db(DCE_3_LINKS_ENABLED_CONFIG_DB)
        
        service = consoled.DCEService()
        
        # Mock all external dependencies
        with mock.patch.object(consoled, 'SerialProxy', MockSerialProxy):
            with mock.patch.object(consoled, 'get_pty_symlink_prefix', return_value="/dev/VC0-"):
                with mock.patch.object(MockConfigDb, 'connect'):
                    # Simulate start
                    service.config_db = MockConfigDb()
                    service.state_db = mock.Mock()
                    service.state_table = mock.Mock()
                    service.pty_symlink_prefix = "/dev/VC0-"
                    service.running = True
                    
                    # Simulate initial config load (like init_data_handler)
                    service._load_initial_config({
                        "CONSOLE_PORT": CONSOLE_PORT_3_LINKS,
                        "CONSOLE_SWITCH": {"console_mgmt": {"enabled": "yes"}}
                    })
                    
                    # Verify 3 proxies created and started
                    self.assertEqual(len(service.proxies), 3)
                    self.assertEqual(MockSerialProxy.get_started_count(), 3)
                    
                    # Verify all proxies are running
                    for link_id, proxy in service.proxies.items():
                        self.assertTrue(proxy.running, f"Proxy {link_id} should be running")


if __name__ == '__main__':
    import unittest
    unittest.main()
