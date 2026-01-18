# 向 sonic-host-services 添加新服务指南

## 概述

本文档说明如何向 sonic-host-services 项目添加一个新的系统服务（如 console-monitor）。

## 项目结构

sonic-host-services 包含两种类型的服务：

1. **独立守护进程**：直接运行的 Python 脚本（如 hostcfgd, featured, caclmgrd）
2. **D-Bus 模块**：通过 sonic-host-server 注册的 D-Bus 服务（如 image_service, reboot）

## 添加新服务的步骤

### 1. 创建服务脚本

在 `scripts/` 目录创建服务脚本：

```bash
scripts/console-monitor
```

确保脚本：
- 有执行权限（`chmod +x`）
- 包含 shebang（`#!/usr/bin/env python3`）
- 可以独立运行

### 2. 更新 setup.py

在 `setup.py` 的 `scripts` 列表中添加新脚本：

```python
scripts=[
    'scripts/caclmgrd',
    'scripts/hostcfgd',
    'scripts/featured',
    # ... 其他脚本 ...
    'scripts/console-monitor',  # 添加这行
],
```

**作用**：使用 `pip install` 或 `setup.py install` 时，脚本会被安装到 `/usr/local/bin/`

### 3. 创建 systemd service 文件

在 `data/debian/` 目录创建 service 文件：

**DCE 模式**：`data/debian/sonic-host-services-data.console-monitor-dce.service`

```ini
[Unit]
Description=Console Monitor DCE Service - Proxy and Heartbeat Detection
Documentation=https://github.com/wiperi/consoled
After=config-setup.service database.service
Requires=config-setup.service database.service

[Service]
Type=simple
ExecStart=/usr/bin/console-monitor dce
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

SupplementaryGroups=dialout

[Install]
WantedBy=multi-user.target
```

**DTE 模式**：`data/debian/sonic-host-services-data.console-monitor-dte.service`

```ini
[Unit]
Description=Console Monitor DTE Service - Heartbeat Sender
Documentation=https://github.com/wiperi/consoled
After=config-setup.service database.service
Requires=config-setup.service database.service

[Service]
Type=simple
ExecStart=/usr/bin/console-monitor dte
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**注意事项**：
- 文件名必须以 `sonic-host-services-data.` 为前缀
- 后缀必须是 `.service`
- 中间部分是服务名（用于 `systemctl` 命令）

### 4. 更新 debian/rules

在 `data/debian/rules` 的 `override_dh_installsystemd` 中添加新服务：

```makefile
override_dh_installsystemd:
	dh_installsystemd --no-start --name=caclmgrd
	dh_installsystemd --no-start --name=hostcfgd
	dh_installsystemd --no-start --name=featured
	# ... 其他服务 ...
	dh_installsystemd --no-start --name=console-monitor-dce
	dh_installsystemd --no-start --name=console-monitor-dte
```

**参数说明**：
- `--no-start`：打包后不自动启动服务
- `--no-enable`：打包后不自动启用开机自启
- `--name=<service>`：服务名（不含 `sonic-host-services-data.` 前缀和 `.service` 后缀）

### 5. 创建测试用例

在 `tests/` 目录创建测试文件：

```bash
tests/console_monitor/
├── __init__.py
├── console_monitor_test.py
├── test_vectors.py
└── Console-Monitor-Test-Plan.md
```

测试文件应该：
- 使用 pytest 框架
- 使用 MockConfigDb 模拟 Redis
- 包含完整的单元测试和集成测试

### 6. 更新文档

创建或更新以下文档：

```bash
docs/
├── Console-Monitor-HLD-CN.md      # 高层设计文档（中文）
├── Console-Monitor-HLD.md         # 高层设计文档（英文）
└── TestPlan.md                    # 测试计划
```

## 文件安装位置

执行 `dpkg-buildpackage` 构建 Debian 包后，文件会被安装到：

| 源文件位置 | 安装位置 | 说明 |
|-----------|---------|------|
| `scripts/console-monitor` | `/usr/local/bin/console-monitor` | 可执行脚本（通过 setup.py） |
| `data/debian/*.service` | `/lib/systemd/system/*.service` | systemd 服务文件 |
| `data/templates/*.j2` | `/usr/share/sonic/templates/` | Jinja2 模板文件 |
| `data/org.sonic.hostservice.conf` | `/etc/dbus-1/system.d/` | D-Bus 配置文件 |

## 构建和测试流程

### 本地开发测试

```bash
# 1. 运行单元测试
python3 -m pytest tests/console_monitor/ -v

# 2. 代码覆盖率测试
python3 -m pytest tests/console_monitor/ --cov=scripts/console-monitor --cov-report=html

# 3. 手动运行服务（调试）
sudo python3 scripts/console-monitor dce
sudo python3 scripts/console-monitor dte
```

### 构建 Debian 包

```bash
# 在 data/ 目录构建
cd data/
dpkg-buildpackage -rfakeroot -b -us -uc

# 生成的包：
# sonic-host-services-data_1.0_all.deb
```

### 安装和验证

```bash
# 1. 安装包
sudo dpkg -i sonic-host-services-data_1.0_all.deb

# 2. 检查服务文件
ls -la /lib/systemd/system/console-monitor*.service

# 3. 重新加载 systemd
sudo systemctl daemon-reload

# 4. 启动服务
sudo systemctl start console-monitor-dce.service
sudo systemctl start console-monitor-dte.service

# 5. 查看状态
sudo systemctl status console-monitor-dce.service
sudo systemctl status console-monitor-dte.service

# 6. 查看日志
sudo journalctl -u console-monitor-dce.service -f
sudo journalctl -u console-monitor-dte.service -f
```

## 常见问题

### Q1: 服务脚本找不到模块

**问题**：服务启动时报 `ModuleNotFoundError`

**解决**：
- 确保在 `setup.py` 中正确定义了 `packages` 和 `package_dir`
- 运行 `sudo python3 setup.py install` 安装依赖
- 检查脚本的 `sys.path` 是否包含模块路径

### Q2: systemd 服务无法启动

**问题**：`systemctl start` 失败

**解决**：
1. 检查 service 文件语法：`systemd-analyze verify <service-file>`
2. 查看详细日志：`journalctl -xe`
3. 确认 `ExecStart` 路径正确
4. 检查依赖服务是否已启动（`After=`, `Requires=`）

### Q3: dh_installsystemd 找不到 service 文件

**问题**：构建包时报错 `Cannot find ...`

**解决**：
- 确认 service 文件名格式：`sonic-host-services-data.<name>.service`
- 确认 `--name=` 参数与文件名中间部分一致
- 文件必须在 `data/debian/` 目录

## 参考资料

- [Debian systemd 打包指南](https://wiki.debian.org/systemd/Packaging)
- [dh_installsystemd 文档](https://manpages.debian.org/testing/debhelper/dh_installsystemd.1.en.html)
- [SONiC 开发者文档](https://github.com/sonic-net/SONiC/wiki)
- [本项目现有服务](../scripts/)

## 检查清单

添加新服务前，确保完成以下步骤：

- [ ] 创建服务脚本 `scripts/<service-name>`
- [ ] 更新 `setup.py` 的 `scripts` 列表
- [ ] 创建 systemd service 文件 `data/debian/sonic-host-services-data.<name>.service`
- [ ] 更新 `data/debian/rules` 的 `override_dh_installsystemd`
- [ ] 创建完整的测试用例 `tests/<service_name>/`
- [ ] 编写高层设计文档（HLD）
- [ ] 编写测试计划（Test Plan）
- [ ] 本地运行测试并通过
- [ ] 构建 Debian 包并验证安装
- [ ] 验证服务启动和运行

---

**最后更新**：2026-01-18
