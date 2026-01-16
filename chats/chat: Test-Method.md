# Testing and Quality Assurance

This document covers the comprehensive testing framework for the sonic-host-services repository, including unit test infrastructure, mock frameworks, test data structures, and quality assurance practices.

## Table of Contents

- [Testing Architecture Overview](#testing-architecture-overview)
- [Quick Start](#quick-start)
- [Test Configuration](#test-configuration)
- [Mock Infrastructure](#mock-infrastructure)
- [Test Organization](#test-organization)
- [Writing Tests](#writing-tests)
- [Coverage Reports](#coverage-reports)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Testing Architecture Overview

The sonic-host-services testing framework is built around **pytest** with comprehensive mocking infrastructure to simulate SONiC database interactions and system dependencies.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Test Architecture                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │   pytest    │───▶│   Test      │───▶│  Mock Infrastructure    │ │
│  │  Framework  │    │   Files     │    │                         │ │
│  └─────────────┘    └─────────────┘    │  • MockConfigDb         │ │
│        │                               │  • MockSelect           │ │
│        │                               │  • MockSubscriberState  │ │
│        ▼                               │  • MockDBConnector      │ │
│  ┌─────────────┐                       │  • MockRestartWaiter    │ │
│  │  Coverage   │                       └─────────────────────────┘ │
│  │  Reports    │                                                   │
│  │ (HTML/XML)  │                                                   │
│  └─────────────┘                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Install Dependencies

```bash
# Install test dependencies
pip install pytest pytest-cov parameterized pyfakefs deepdiff

# Install package in development mode
pip install -e .
```

### Run All Tests

```bash
# Run all tests with coverage
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/featured/featured_test.py -v

# Run specific test class
python -m pytest tests/host_modules/reboot_test.py::TestReboot -v

# Run specific test method
python -m pytest tests/host_modules/reboot_test.py::TestReboot::test_populate_reboot_status_flag -v
```

### Run Tests with Custom Coverage

```bash
# Override pytest.ini coverage settings
python -m pytest tests/ --cov=scripts/featured --cov-report=term-missing
```

---

## Test Configuration

### pytest.ini

The testing infrastructure is configured through `pytest.ini`:

```ini
[pytest]
addopts = --cov=scripts --cov=host_modules --cov-report html --cov-report term --cov-report xml --ignore=tests/*/test*_vectors.py --junitxml=test-results.xml -vv
```

| Option | Value | Purpose |
|--------|-------|---------|
| `--cov` | `scripts --cov=host_modules` | Coverage for main code directories |
| `--cov-report` | `html term xml` | Multiple coverage report formats |
| `--ignore` | `tests/*/test*_vectors.py` | Exclude test data from coverage |
| `--junitxml` | `test-results.xml` | CI/CD integration output |
| `-vv` | Verbose output | Detailed test execution information |

---

## Mock Infrastructure

The testing framework provides sophisticated mock implementations that simulate SONiC database operations without requiring actual Redis databases.

### MockConfigDb

Located in `tests/common/mock_configdb.py`, this class simulates SONiC's ConfigDBConnector:

```python
from tests.common.mock_configdb import MockConfigDb

class TestMyFeature:
    def test_example(self):
        # Set up test data
        MockConfigDb.set_config_db({
            'FEATURE': {
                'my_feature': {
                    'state': 'enabled',
                    'auto_restart': 'enabled'
                }
            }
        })
        
        # Your test code here
        mock_db = MockConfigDb()
        table = mock_db.get_table('FEATURE')
        assert table['my_feature']['state'] == 'enabled'
```

**Key Features:**

| Method | Description |
|--------|-------------|
| `set_config_db(data)` | Initialize CONFIG_DB with test data |
| `mod_config_db(data)` | Update existing CONFIG_DB data |
| `get_config_db()` | Retrieve current CONFIG_DB state |
| `get_table(table_name)` | Get all entries from a table |
| `get_entry(key, field)` | Get specific entry |
| `set_entry(key, field, data)` | Set specific entry |
| `subscribe(table_name, callback)` | Register change handler |

### MockSelect

Simulates SONiC's event selection mechanism:

```python
from tests.common.mock_configdb import MockSelect

class TestEventHandling:
    def test_feature_change(self):
        # Set up event queue
        MockSelect.set_event_queue([
            ('FEATURE', 'dhcp_relay'),
            ('FEATURE', 'snmp')
        ])
        
        # Your test code processes events
        # ...
        
        # Clean up
        MockSelect.reset_event_queue()
```

**Key Features:**

| Method | Description |
|--------|-------------|
| `set_event_queue(events)` | Set list of events to simulate |
| `get_event_queue()` | Get current event queue |
| `reset_event_queue()` | Clear event queue |
| `select(timeout)` | Simulate event selection |

### MockSubscriberStateTable

Simulates SONiC's SubscriberStateTable for CONFIG_DB change notifications:

```python
from tests.common.mock_configdb import MockSubscriberStateTable

# Used internally by tests to simulate table subscriptions
subscriber = MockSubscriberStateTable(conn, 'FEATURE')
key, op, fvs = subscriber.pop()  # Returns: ('feature_name', 'SET', {...})
```

### MockRestartWaiter

Located in `tests/common/mock_restart_waiter.py`, simulates warm/fast boot detection:

```python
from tests.common.mock_restart_waiter import MockRestartWaiter

# Simulate advanced boot mode
MockRestartWaiter.advancedReboot = True
```

---

## Test Organization

### Directory Structure

```
tests/
├── __init__.py
├── common/                          # Shared mock infrastructure
│   ├── mock_configdb.py            # MockConfigDb, MockSelect, etc.
│   ├── mock_restart_waiter.py      # MockRestartWaiter
│   └── mock_bootloader.py          # Boot loader mocks
│
├── featured/                        # featured daemon tests
│   ├── featured_test.py            # Test cases
│   └── test_vectors.py             # Test data
│
├── hostcfgd/                        # hostcfgd daemon tests
│   ├── hostcfgd_test.py
│   └── test_vectors.py
│
├── caclmgrd/                        # caclmgrd daemon tests
│   ├── caclmgrd_test.py            # Core tests
│   ├── caclmgrd_bfd_test.py        # BFD-specific tests
│   ├── caclmgrd_dhcp_test.py       # DHCP-specific tests
│   └── test_*_vectors.py           # Various test vectors
│
├── host_modules/                    # D-Bus host module tests
│   ├── reboot_test.py
│   ├── docker_service_test.py
│   ├── image_service_test.py
│   ├── gcu_test.py
│   └── ...
│
├── check_platform_test.py           # Platform check tests
├── procdockerstatsd_test.py         # Process stats tests
└── gnoi_reset_test.py               # gNOI reset tests
```

### Test Vectors

Test vectors provide comprehensive configuration scenarios. They are stored in `test_vectors.py` files:

```python
# tests/hostcfgd/test_vectors.py

HOSTCFG_DAEMON_INIT_CFG_DB = {
    'DEVICE_METADATA': {
        'localhost': {}
    },
    'FEATURE': {},
    'AAA': {},
    'TACPLUS': {},
    # ... minimal configuration
}

HOSTCFG_DAEMON_CFG_DB = {
    'DEVICE_METADATA': {
        'localhost': {
            'subtype': 'DualToR',
            'hostname': 'SomeNewHostname',
            'timezone': 'Europe/Kyiv'
        }
    },
    'NTP': {
        'global': {
            'vrf': 'default',
            'src_intf': 'eth0;Loopback0'
        }
    },
    # ... comprehensive test data
}
```

---

## Writing Tests

### Basic Test Structure

```python
import pytest
from unittest import mock
from tests.common.mock_configdb import MockConfigDb

class TestMyFeature:
    """Test cases for MyFeature"""
    
    @classmethod
    def setup_class(cls):
        """Set up test fixtures"""
        MockConfigDb.set_config_db({
            'MY_TABLE': {'key1': {'field': 'value'}}
        })
    
    @classmethod
    def teardown_class(cls):
        """Clean up after tests"""
        MockConfigDb.CONFIG_DB = None
    
    def test_basic_functionality(self):
        """Test basic feature behavior"""
        # Arrange
        expected = 'value'
        
        # Act
        db = MockConfigDb()
        result = db.get_entry('MY_TABLE', 'key1')
        
        # Assert
        assert result['field'] == expected
```

### Testing with Parameterization

```python
from parameterized import parameterized

class TestFeatureHandler:
    
    @parameterized.expand([
        ("DualTorCase", DUAL_TOR_CONFIG),
        ("SingleToRCase", SINGLE_TOR_CONFIG),
        ("T1Case", T1_CONFIG),
    ])
    def test_handler(self, test_name, config_data):
        """Test handler with various configurations"""
        MockConfigDb.set_config_db(config_data['config_db'])
        # ... test implementation
```

### Testing with pyfakefs

For tests requiring filesystem operations:

```python
from pyfakefs.fake_filesystem_unittest import patchfs

class TestSystemdConfig:
    
    @patchfs
    def test_create_config_file(self, fs):
        """Test systemd config file creation"""
        # Create required directories
        fs.create_dir('/etc/systemd/system/')
        
        # Your test code that writes files
        # ...
        
        # Assert file exists and has correct content
        assert os.path.exists('/etc/systemd/system/my.service.d/auto_restart.conf')
```

### Testing D-Bus Host Modules

```python
class TestReboot:
    
    @classmethod
    def setup_class(cls):
        with mock.patch("reboot.super") as mock_host_module:
            cls.reboot_module = Reboot(MOD_NAME)
    
    def test_valid_reboot_request(self):
        """Test valid cold reboot request"""
        request = '{"method": 1, "message": "test reboot"}'
        
        with mock.patch('reboot.threading.Thread') as mock_thread:
            return_code, response = self.reboot_module.issue_reboot(request)
        
        assert return_code == 0
        response_data = json.loads(response)
        assert response_data['active'] == True
```

---

## Coverage Reports

### Generated Reports

After running tests, coverage reports are generated in multiple formats:

| Format | Location | Purpose |
|--------|----------|---------|
| HTML | `htmlcov/index.html` | Interactive browsing |
| Terminal | stdout | Immediate feedback |
| XML | `coverage.xml` | CI/CD integration |
| JUnit | `test-results.xml` | Build system integration |

### Viewing HTML Coverage

```bash
# Run tests to generate coverage
python -m pytest tests/ -v

# Open HTML report in browser
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html       # macOS
```

### Coverage Example Output

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
host_modules/config_engine.py        35     10    71%
host_modules/docker_service.py      117     25    79%
host_modules/reboot.py              140     30    79%
scripts/featured                    393    100    75%
scripts/hostcfgd                   2540    500    80%
-----------------------------------------------------
TOTAL                              3225    665    79%
```

---

## CI/CD Integration

### Azure Pipelines

The project uses Azure Pipelines for CI/CD. Test results are integrated via:

- `test-results.xml`: JUnit format test results
- `coverage.xml`: Cobertura format coverage data

### Running in CI

```yaml
# azure-pipelines.yml example
- script: |
    pip install -e .
    python -m pytest tests/ --junitxml=test-results.xml --cov-report=xml
  displayName: 'Run Tests'

- task: PublishTestResults@2
  inputs:
    testResultsFiles: 'test-results.xml'
    
- task: PublishCodeCoverageResults@1
  inputs:
    codeCoverageTool: 'Cobertura'
    summaryFileLocation: 'coverage.xml'
```

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError

```
ModuleNotFoundError: No module named 'sonic_py_common'
```

**Solution:** Install SONiC dependencies from sonic-buildimage or mock them:

```python
sys.modules['sonic_py_common'] = mock.MagicMock()
```

#### 2. Platform Directory Not Found

```
OSError: Failed to locate platform directory
```

**Solution:** Mock the `device_info.get_num_dpus()` function:

```python
with mock.patch('sonic_py_common.device_info.get_num_dpus', return_value=0):
    # Your test code
```

#### 3. Redis Connection Error

**Solution:** Use MockConfigDb instead of real ConfigDBConnector:

```python
import featured
featured.ConfigDBConnector = MockConfigDb
```

#### 4. Tests Hanging on Select

**Solution:** Set up event queue and timeout handling:

```python
MockSelect.set_event_queue([('TABLE', 'key')])
MockSelect.NUM_TIMEOUT_TRIES = 1
```

### Debug Mode

Enable verbose logging in tests:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or run pytest with extra verbosity:

```bash
python -m pytest tests/ -vvv --tb=long
```

---

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pyfakefs Documentation](https://pytest-pyfakefs.readthedocs.io/)
- [SONiC Architecture](https://github.com/sonic-net/SONiC/wiki/Architecture)
