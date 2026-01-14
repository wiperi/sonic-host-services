# CLAUDE.md - sonic-host-services

## Project Overview

**sonic-host-services** is a collection of Python daemons and host modules that run in the SONiC (Software for Open Networking in the Cloud) host OS. These services provide critical system management functionality including configuration management, feature control, access control, reboot handling, and docker-to-host communication via D-Bus.

---

## Project Structure

```
sonic-host-services/
├── scripts/                    # Daemon scripts (main executables)
│   ├── hostcfgd               # Host configuration daemon
│   ├── featured               # Feature management daemon
│   ├── caclmgrd               # Control plane ACL manager daemon
│   ├── procdockerstatsd       # Process/Docker statistics daemon
│   ├── aaastatsd              # AAA (RADIUS/TACACS+) statistics daemon
│   ├── sonic-host-server      # D-Bus host service server
│   ├── determine-reboot-cause # Reboot cause detection script
│   ├── process-reboot-cause   # Reboot cause processing script
│   ├── gnoi_shutdown_daemon.py # gNOI shutdown handler
│   ├── ldap.py                # LDAP configuration helper
│   ├── check_platform.py      # Platform check utility
│   └── wait-for-sonic-core.sh # Startup wait script
│
├── host_modules/              # D-Bus service modules
│   ├── host_service.py        # Base class for D-Bus modules
│   ├── config_engine.py       # Config reload/save handler
│   ├── docker_service.py      # Docker container management
│   ├── file_service.py        # File operations (stat, download)
│   ├── gcu.py                 # Generic Config Updater
│   ├── gnoi_reset.py          # gNOI factory reset handler
│   ├── image_service.py       # SONiC image download/install
│   ├── reboot.py              # Reboot execution handler
│   ├── showtech.py            # Show tech-support handler
│   ├── systemd_service.py     # Systemd service control
│   └── debug_service.py       # Debug execution service
│
├── utils/                     # Utility modules
│   └── run_cmd.py             # Command execution helper
│
├── tests/                     # Unit tests (pytest)
│   ├── caclmgrd/              # caclmgrd tests
│   ├── featured/              # featured tests
│   ├── hostcfgd/              # hostcfgd tests
│   ├── host_modules/          # host_modules tests
│   └── common/                # Common test utilities
│
├── data/                      # D-Bus configuration files
│   └── templates/             # Jinja2 templates
│
└── debian/                    # Debian packaging files
```

---

## Key Daemons

### 1. hostcfgd (Host Configuration Daemon)
- **File**: [scripts/hostcfgd](scripts/hostcfgd)
- **Purpose**: Monitors CONFIG_DB and applies host-level configurations
- **Key Features**:
  - AAA (Authentication, Authorization, Accounting): TACACS+, RADIUS, LDAP
  - SSH configuration (ciphers, MACs, authentication settings)
  - PAM configuration management
  - Password policies and user management
  - Timezone configuration

### 2. featured (Feature Daemon)
- **File**: [scripts/featured](scripts/featured)
- **Purpose**: Manages SONiC feature services (enable/disable/auto-restart)
- **Key Features**:
  - Watches FEATURE table in CONFIG_DB
  - Controls systemd services based on feature state
  - Handles delayed service startup (waits for PortInitDone)
  - Supports multi-ASIC and DPU configurations
  - Manages auto-restart configurations

### 3. caclmgrd (Control Plane ACL Manager Daemon)
- **File**: [scripts/caclmgrd](scripts/caclmgrd)
- **Purpose**: Manages iptables rules for control plane ACLs
- **Key Features**:
  - Converts CONFIG_DB ACL rules to iptables
  - Supports IPv4 and IPv6
  - Handles service-specific ACLs (SSH, SNMP, NTP, etc.)
  - Multi-namespace support for multi-ASIC platforms

### 4. procdockerstatsd (Process/Docker Statistics Daemon)
- **File**: [scripts/procdockerstatsd](scripts/procdockerstatsd)
- **Purpose**: Collects and publishes process/container statistics to STATE_DB
- **Key Features**:
  - Docker container resource usage (CPU, memory, network I/O)
  - Process statistics collection

### 5. sonic-host-server (D-Bus Host Service)
- **File**: [scripts/sonic-host-server](scripts/sonic-host-server)
- **Purpose**: D-Bus server for docker-to-host communication
- **Key Features**:
  - Registers host_modules as D-Bus endpoints
  - Enables containers to execute privileged host operations
  - Bus name: `org.SONiC.HostService`

---

## Host Modules (D-Bus Services)

| Module | D-Bus Name | Purpose |
|--------|------------|---------|
| `config_engine.py` | `org.SONiC.HostService.config` | Config reload/save |
| `reboot.py` | `org.SONiC.HostService.reboot` | System reboot (cold/warm/halt) |
| `docker_service.py` | `org.SONiC.HostService.docker_service` | Docker container management |
| `image_service.py` | `org.SONiC.HostService.image_service` | SONiC image download/install |
| `gcu.py` | `org.SONiC.HostService.gcu` | Generic Config Updater patches |
| `gnoi_reset.py` | `org.SONiC.HostService.gnoi_reset` | gNOI factory reset |
| `systemd_service.py` | `org.SONiC.HostService.systemd` | Systemd service restart/stop |
| `file_service.py` | `org.SONiC.HostService.file` | File stat/download operations |
| `showtech.py` | `org.SONiC.HostService.showtech` | Show tech-support execution |

---

## Technical Stack

- **Language**: Python 3
- **IPC**: D-Bus (dbus-python, PyGObject)
- **Database**: Redis via swsscommon (CONFIG_DB, STATE_DB, APPL_DB)
- **Templates**: Jinja2 (for configuration rendering)
- **Process Management**: systemd
- **Container**: Docker
- **Testing**: pytest with pytest-cov

---

## Key Dependencies

```python
# SONiC packages (must be built from sonic-buildimage)
sonic-py-common      # Common SONiC Python utilities
sonic-utilities      # SONiC CLI utilities
swsscommon           # Redis database connector

# Standard packages
dbus-python          # D-Bus Python bindings
systemd-python       # systemd Python bindings
Jinja2               # Template engine
PyGObject            # GObject introspection
docker               # Docker SDK
psutil               # Process utilities
```

---

## Database Interactions

### CONFIG_DB (db=4)
- `FEATURE` - Feature enable/disable/auto-restart states
- `AAA` - Authentication configuration
- `TACPLUS_SERVER` - TACACS+ server settings
- `RADIUS_SERVER` - RADIUS server settings
- `ACL_TABLE` / `ACL_RULE` - Control plane ACL rules
- `DEVICE_METADATA` - Device type and configuration
- `SSH_SERVER` - SSH daemon configuration

### STATE_DB (db=6)
- `FEATURE` - Runtime feature states
- `DOCKER_STATS` - Container statistics
- `PROCESS_STATS` - Process statistics

---

## Running Tests

```bash
# Run all tests with coverage
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/featured/featured_test.py -v

# Run with coverage report
python -m pytest tests/ --cov=scripts --cov=host_modules --cov-report=term-missing
```

### Test Requirements
Tests require mocking SONiC-specific components:
- `swsscommon.ConfigDBConnector`
- `sonic_py_common.device_info`
- Platform directory structures

---

## Common Development Tasks

### Adding a New Host Module
1. Create new module in `host_modules/` inheriting from `HostModule`
2. Define D-Bus methods using `@host_service.method()` decorator
3. Register in `scripts/sonic-host-server` `register_dbus()` function
4. Add unit tests in `tests/host_modules/`

### Modifying hostcfgd
1. Add handler class or method in `scripts/hostcfgd`
2. Register table subscription in the daemon
3. Update Jinja2 templates if needed (in `/usr/share/sonic/templates/`)

### Adding Feature Management Logic
1. Modify `FeatureHandler` class in `scripts/featured`
2. Handle new feature states or configuration options
3. Update systemd service configurations as needed

---

## Coding Conventions

- Follow PEP 8 style guidelines
- Use type hints where applicable
- Use `syslog` for logging in daemons
- Use `logging` module in host_modules
- Error codes should use `errno` constants where appropriate
- D-Bus methods return `(int, str)` tuple: `(return_code, message)`

---

## Architecture Notes

### D-Bus Communication Flow
```
Container (e.g., GNMI) 
    → D-Bus call to org.SONiC.HostService.<module>
    → sonic-host-server receives request
    → host_module executes privileged operation
    → Returns result via D-Bus
```

### Feature State Machine
```
CONFIG_DB FEATURE table
    → featured daemon monitors changes
    → Renders Jinja2 templates for dynamic states
    → Controls systemd units (start/stop/enable/disable)
    → Updates STATE_DB with runtime state
```

### Control Plane ACL Flow
```
CONFIG_DB ACL_TABLE/ACL_RULE
    → caclmgrd monitors changes
    → Translates to iptables rules
    → Applies via subprocess (iptables/ip6tables)
```
