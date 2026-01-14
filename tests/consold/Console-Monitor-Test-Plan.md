# Console Monitor (consoled) Test Plan

## Table of Contents

- [Overview](#overview)
- [Test Environment](#test-environment)
- [Test Categories](#test-categories)
- [Test Cases](#test-cases)
  - [DCE Service Tests](#dce-service-tests)
  - [DTE Service Tests](#dte-service-tests)
  - [Frame Protocol Tests](#frame-protocol-tests)
  - [FrameFilter Tests](#framefilter-tests)
  - [Integration Tests](#integration-tests)
- [Test Data](#test-data)
- [Running Tests](#running-tests)
- [Coverage Goals](#coverage-goals)

---

## Overview

This document describes the test plan for the Console Monitor service (`consoled`), which provides link operational state detection between Console Server (DCE) and SONiC Switch (DTE) via serial ports.

### Component Under Test

| Component | Description |
|-----------|-------------|
| `scripts/consoled` | Main console monitor service |
| `DCEService` | Console Server side service - manages serial proxies |
| `DTEService` | SONiC Switch side service - sends heartbeat frames |
| `SerialProxy` | Per-port serial proxy with PTY bridge |
| `Frame` | Heartbeat frame protocol implementation |
| `FrameFilter` | Byte stream parser for frame detection |

### References

- [SONiC Console Switch High Level Design](../../../consoled/docs/SONiC-Console-Switch-High-Level-Design.md)
- [Console Monitor HLD (Chinese)](../../../consoled/docs/Console-Monitor-HLD-CN.md)

---

## Test Environment

### Dependencies

```bash
pip install pytest pytest-cov parameterized pyfakefs deepdiff
```

### Mock Infrastructure

| Mock Class | Purpose |
|------------|---------|
| `MockConfigDb` | Simulates SONiC ConfigDBConnector |
| `MockDBConnector` | Simulates SONiC DBConnector |
| `MockSerialProxy` | Simulates SerialProxy without actual I/O |

### Test Data Location

- Test vectors: `tests/consold/test_vectors.py`
- Test cases: `tests/consold/consoled_test.py`

---

## Test Categories

| Category | Description | Priority |
|----------|-------------|----------|
| Unit Tests | Individual function/class testing | P0 |
| Integration Tests | Component interaction testing | P1 |
| E2E Tests | Full system testing with hardware | P2 |

---

## Test Cases

### DCE Service Tests

DCE (Data Communications Equipment) service runs on the Console Server side.

| ID | Test Case | Description | Status |
|----|-----------|-------------|--------|
| DCE-001 | `test_dce_service_initialization` | Verify DCE service can be initialized correctly | ✅ Implemented |
| DCE-002 | `test_dce_check_feature_enabled_when_enabled` | Verify `_check_feature_enabled()` returns True when `CONSOLE_SWITCH|console_mgmt.enabled=yes` | ✅ Implemented |
| DCE-003 | `test_dce_check_feature_enabled_when_disabled` | Verify `_check_feature_enabled()` returns False when `CONSOLE_SWITCH|console_mgmt.enabled=no` | ✅ Implemented |
| DCE-004 | `test_dce_get_all_configs_parses_correctly` | Verify `_get_all_configs()` correctly parses CONSOLE_PORT table with 3 ports | ✅ Implemented |
| DCE-005 | `test_dce_sync_creates_proxies_when_enabled` | Verify `_sync()` creates SerialProxy for each configured port when feature enabled | ✅ Implemented |
| DCE-006 | `test_dce_sync_creates_no_proxies_when_disabled` | Verify `_sync()` creates no proxies when feature disabled | ✅ Implemented |
| DCE-007 | `test_dce_sync_removes_proxy_when_port_deleted` | Verify `_sync()` removes proxy when port config is deleted | ✅ Implemented |
| DCE-008 | `test_dce_console_port_handler_triggers_sync` | Verify `console_port_handler()` triggers `_sync()` on config change | ✅ Implemented |
| DCE-009 | `test_dce_console_switch_handler_triggers_sync` | Verify `console_switch_handler()` triggers `_sync()` on feature toggle | ✅ Implemented |
| DCE-010 | `test_dce_start_connects_to_databases` | Verify `start()` connects to CONFIG_DB and STATE_DB | ⬜ Not Implemented |
| DCE-011 | `test_dce_stop_cleans_up_all_proxies` | Verify `stop()` stops all proxies and cleans up resources | ⬜ Not Implemented |
| DCE-012 | `test_dce_register_callbacks_subscribes_tables` | Verify `register_callbacks()` subscribes to CONSOLE_PORT and CONSOLE_SWITCH tables | ⬜ Not Implemented |
| DCE-013 | `test_dce_baud_rate_change_restarts_proxy` | Verify proxy is restarted when baud_rate changes | ⬜ Not Implemented |

### DTE Service Tests

DTE (Data Terminal Equipment) service runs on the SONiC Switch side.

| ID | Test Case | Description | Status |
|----|-----------|-------------|--------|
| DTE-001 | `test_dte_service_initialization` | Verify DTE service can be initialized with TTY and baud | ⬜ Not Implemented |
| DTE-002 | `test_dte_check_enabled_returns_true` | Verify `_check_enabled()` returns True when `CONSOLE_SWITCH|controlled_device.enabled=yes` | ⬜ Not Implemented |
| DTE-003 | `test_dte_check_enabled_returns_false` | Verify `_check_enabled()` returns False when `CONSOLE_SWITCH|controlled_device.enabled=no` | ⬜ Not Implemented |
| DTE-004 | `test_dte_start_heartbeat_when_enabled` | Verify heartbeat thread starts when feature enabled | ⬜ Not Implemented |
| DTE-005 | `test_dte_stop_heartbeat_when_disabled` | Verify heartbeat thread stops when feature disabled | ⬜ Not Implemented |
| DTE-006 | `test_dte_heartbeat_interval` | Verify heartbeat is sent at configured interval (5s) | ⬜ Not Implemented |
| DTE-007 | `test_dte_parse_proc_cmdline` | Verify `parse_proc_cmdline()` parses console parameters correctly | ⬜ Not Implemented |
| DTE-008 | `test_dte_console_switch_handler_toggles_heartbeat` | Verify handler toggles heartbeat on/off based on config | ⬜ Not Implemented |

### Frame Protocol Tests

Tests for the heartbeat frame protocol implementation.

| ID | Test Case | Description | Status |
|----|-----------|-------------|--------|
| FRM-001 | `test_crc16_modbus` | Verify CRC-16/MODBUS calculation is correct | ✅ Implemented |
| FRM-002 | `test_escape_data_escapes_special_chars` | Verify SOF(0x05), EOF(0x00), DLE(0x10) are escaped with DLE prefix | ✅ Implemented |
| FRM-003 | `test_unescape_data_restores_original` | Verify unescape restores original data | ✅ Implemented |
| FRM-004 | `test_frame_build_creates_valid_frame` | Verify `Frame.build()` creates frame with SOF/EOF delimiters | ✅ Implemented |
| FRM-005 | `test_frame_parse_roundtrip` | Verify frame can be built and parsed back correctly | ✅ Implemented |
| FRM-006 | `test_frame_parse_rejects_bad_crc` | Verify `Frame.parse()` returns None for corrupted CRC | ✅ Implemented |
| FRM-007 | `test_frame_create_heartbeat` | Verify `Frame.create_heartbeat()` creates valid heartbeat frame | ⬜ Not Implemented |
| FRM-008 | `test_frame_is_heartbeat` | Verify `is_heartbeat()` returns correct result | ⬜ Not Implemented |
| FRM-009 | `test_frame_sequence_number_wrap` | Verify sequence number wraps at 256 | ⬜ Not Implemented |

### FrameFilter Tests

Tests for the byte stream frame detection and filtering.

| ID | Test Case | Description | Status |
|----|-----------|-------------|--------|
| FLT-001 | `test_frame_filter_detects_heartbeat` | Verify FrameFilter detects heartbeat frame in byte stream | ✅ Implemented |
| FLT-002 | `test_frame_filter_passes_user_data` | Verify non-frame data is passed to user_data callback | ✅ Implemented |
| FLT-003 | `test_frame_filter_separates_frame_and_data` | Verify mixed frame and user data are correctly separated | ✅ Implemented |
| FLT-004 | `test_frame_filter_handles_partial_frame` | Verify partial frame is handled correctly | ⬜ Not Implemented |
| FLT-005 | `test_frame_filter_timeout_flushes_buffer` | Verify `on_timeout()` flushes pending data | ⬜ Not Implemented |
| FLT-006 | `test_frame_filter_buffer_overflow` | Verify buffer overflow is handled (MAX_FRAME_BUFFER_SIZE) | ⬜ Not Implemented |
| FLT-007 | `test_frame_filter_corrupted_frame_discarded` | Verify corrupted frame is discarded | ⬜ Not Implemented |
| FLT-008 | `test_frame_filter_consecutive_frames` | Verify multiple consecutive frames are detected | ⬜ Not Implemented |

### SerialProxy Tests

Tests for the per-port serial proxy component.

| ID | Test Case | Description | Status |
|----|-----------|-------------|--------|
| PRX-001 | `test_serial_proxy_creates_pty` | Verify PTY master/slave pair is created | ⬜ Not Implemented |
| PRX-002 | `test_serial_proxy_creates_symlink` | Verify PTY symlink is created (e.g., /dev/VC0-1) | ⬜ Not Implemented |
| PRX-003 | `test_serial_proxy_forwards_data_serial_to_pty` | Verify data from serial is forwarded to PTY | ⬜ Not Implemented |
| PRX-004 | `test_serial_proxy_forwards_data_pty_to_serial` | Verify data from PTY is forwarded to serial | ⬜ Not Implemented |
| PRX-005 | `test_serial_proxy_filters_heartbeat` | Verify heartbeat frames are filtered (not passed to PTY) | ⬜ Not Implemented |
| PRX-006 | `test_serial_proxy_updates_state_on_heartbeat` | Verify STATE_DB is updated to "up" on heartbeat | ⬜ Not Implemented |
| PRX-007 | `test_serial_proxy_heartbeat_timeout` | Verify STATE_DB is updated to "down" on timeout (15s) | ⬜ Not Implemented |
| PRX-008 | `test_serial_proxy_stop_removes_symlink` | Verify symlink is removed on stop | ⬜ Not Implemented |
| PRX-009 | `test_serial_proxy_stop_cleans_state_db` | Verify STATE_DB entries are cleaned on stop | ⬜ Not Implemented |

### Integration Tests

Tests for component interactions.

| ID | Test Case | Description | Status |
|----|-----------|-------------|--------|
| INT-001 | `test_dce_proxy_creation_3_links_enabled` | Verify 3 proxies created when 3 ports configured and feature enabled | ✅ Implemented |
| INT-002 | `test_dce_proxy_creation_feature_disabled` | Verify 0 proxies created when feature disabled | ✅ Implemented |
| INT-003 | `test_dce_proxy_creation_no_ports` | Verify 0 proxies created when no ports configured | ✅ Implemented |
| INT-004 | `test_dce_full_initialization_flow` | Verify complete DCE initialization flow with mocked I/O | ✅ Implemented |
| INT-005 | `test_dte_heartbeat_received_by_dce` | Verify DCE receives heartbeat from DTE (E2E) | ⬜ Not Implemented |
| INT-006 | `test_link_state_transitions` | Verify up/down state transitions based on heartbeat | ⬜ Not Implemented |
| INT-007 | `test_config_db_change_triggers_resync` | Verify CONFIG_DB changes trigger proxy resync | ⬜ Not Implemented |

### Utility Function Tests

| ID | Test Case | Description | Status |
|----|-----------|-------------|--------|
| UTL-001 | `test_get_pty_symlink_prefix` | Verify PTY symlink prefix is read from udevprefix.conf | ⬜ Not Implemented |
| UTL-002 | `test_configure_serial` | Verify serial port is configured with correct parameters | ⬜ Not Implemented |
| UTL-003 | `test_configure_pty` | Verify PTY is configured in raw mode | ⬜ Not Implemented |
| UTL-004 | `test_set_nonblocking` | Verify file descriptor is set to non-blocking | ⬜ Not Implemented |

---

## Test Data

### CONFIG_DB Schema

#### CONSOLE_SWITCH Table

```
key = CONSOLE_SWITCH:console_mgmt      ; DCE side feature toggle
key = CONSOLE_SWITCH:controlled_device ; DTE side feature toggle

; field = value
enabled = "yes"/"no"
```

#### CONSOLE_PORT Table

```
key = CONSOLE_PORT:<port_number>

; field = value
baud_rate     = "9600" / "115200" / ...
remote_device = <device_name>
flow_control  = "0" / "1"
```

### Test Vectors

Located in `tests/consold/test_vectors.py`:

| Vector | Description |
|--------|-------------|
| `DCE_3_LINKS_ENABLED_CONFIG_DB` | 3 console ports with feature enabled |
| `DCE_FEATURE_DISABLED_CONFIG_DB` | 3 console ports with feature disabled |
| `DCE_NO_PORTS_CONFIG_DB` | No ports configured |
| `DTE_ENABLED_CONFIG_DB` | DTE feature enabled |
| `DTE_DISABLED_CONFIG_DB` | DTE feature disabled |

---

## Running Tests

### Run All consoled Tests

```bash
cd /home/admin/sonic-host-services
python -m pytest tests/consold/ -v
```

### Run Specific Test Class

```bash
python -m pytest tests/consold/consoled_test.py::TestDCEService -v
```

### Run Specific Test Method

```bash
python -m pytest tests/consold/consoled_test.py::TestDCEService::test_dce_sync_creates_proxies_when_enabled -v
```

### Run with Coverage

```bash
python -m pytest tests/consold/ -v --cov=scripts/consoled --cov-report=term-missing
```

### Run without Coverage (Faster)

```bash
python -m pytest tests/consold/ -v --no-cov
```

---

## Coverage Goals

| Component | Target Coverage | Current Coverage |
|-----------|-----------------|------------------|
| DCEService | 80% | TBD |
| DTEService | 80% | TBD |
| Frame | 90% | TBD |
| FrameFilter | 90% | TBD |
| SerialProxy | 70% | TBD |
| Utility Functions | 80% | TBD |

---

## Test Summary

| Category | Total | Implemented | Not Implemented |
|----------|-------|-------------|-----------------|
| DCE Service | 13 | 9 | 4 |
| DTE Service | 8 | 0 | 8 |
| Frame Protocol | 9 | 6 | 3 |
| FrameFilter | 8 | 3 | 5 |
| SerialProxy | 9 | 0 | 9 |
| Integration | 7 | 4 | 3 |
| Utility | 4 | 0 | 4 |
| **Total** | **58** | **22** | **36** |

### Implementation Progress

```
[██████████░░░░░░░░░░] 38% Complete (22/58 test cases)
```

---

## Appendix

### A. Mock Class Implementation

See `tests/consold/consoled_test.py` for `MockSerialProxy` implementation.

### B. Adding New Tests

1. Add test vector to `test_vectors.py` if needed
2. Add test case to appropriate test class in `consoled_test.py`
3. Update this document with new test case entry
4. Run tests to verify

### C. Test Naming Convention

```
test_<component>_<action>_<expected_result>

Examples:
- test_dce_sync_creates_proxies_when_enabled
- test_frame_parse_rejects_bad_crc
- test_dte_heartbeat_interval
```
