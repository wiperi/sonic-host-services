# Console Monitor 集成到 sonic-host-services

## 完成的步骤

### 1. ✅ 服务脚本
- **位置**: `scripts/console-monitor`
- **状态**: 已存在，从 consoled 项目复制

### 2. ✅ 更新 setup.py
```python
scripts=[
    # ... 其他脚本 ...
    'scripts/console-monitor'  # 第54行
]
```

### 3. ✅ 创建 systemd service 文件

#### DCE 服务
- **文件**: `data/debian/sonic-host-services-data.console-monitor-dce.service`
- **安装位置**: `/lib/systemd/system/console-monitor-dce.service`
- **功能**: Console Server 侧代理和心跳检测

#### DTE 服务
- **文件**: `data/debian/sonic-host-services-data.console-monitor-dte.service`
- **安装位置**: `/lib/systemd/system/console-monitor-dte.service`
- **功能**: SONiC Switch 侧心跳发送

### 4. ✅ 更新 debian/rules
```makefile
override_dh_installsystemd:
    # ... 其他服务 ...
    dh_installsystemd --no-start --name=console-monitor-dce  # 第24行
    dh_installsystemd --no-start --name=console-monitor-dte  # 第25行
```

### 5. ✅ 测试用例
- **位置**: `tests/console_monitor/`
- **文件**: 
  - `console_monitor_test.py` - 主测试文件
  - `test_vectors.py` - 测试数据
  - `Console-Monitor-Test-Plan.md` - 测试计划

### 6. ✅ 文档
- `docs/Adding-New-Service-Guide.md` - 添加服务指南

## 服务配置对比

| 配置项 | DCE | DTE |
|--------|-----|-----|
| Description | Console Monitor DCE Service | Console Monitor DTE Service |
| ExecStart | `/usr/local/bin/console-monitor dce` | `/usr/local/bin/console-monitor dte` |
| Restart | always (10s) | always (5s) |
| Dependencies | config-setup.service, database.service | config-setup.service, database.service |
| WantedBy | sonic.target | sonic.target |
| SupplementaryGroups | dialout | - |

## 构建和安装

### 构建 Debian 包

```bash
cd /home/admin/sonic-host-services/data
dpkg-buildpackage -rfakeroot -b -us -uc
```

生成的包：
- `sonic-host-services-data_1.0_all.deb`

### 安装包

```bash
sudo dpkg -i sonic-host-services-data_1.0_all.deb
```

### 验证安装

```bash
# 检查服务文件
ls -la /lib/systemd/system/console-monitor*.service

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start console-monitor-dce.service  # DCE 侧
sudo systemctl start console-monitor-dte.service  # DTE 侧

# 查看状态
sudo systemctl status console-monitor-dce.service
sudo systemctl status console-monitor-dte.service

# 查看日志
sudo journalctl -u console-monitor-dce.service -f
sudo journalctl -u console-monitor-dte.service -f
```

## Git 变更总结

```bash
# 修改的文件
M  data/debian/rules                  # 添加 systemd 安装配置
M  setup.py                           # 添加 console-monitor 脚本

# 新增的文件
A  data/debian/sonic-host-services-data.console-monitor-dce.service
A  data/debian/sonic-host-services-data.console-monitor-dte.service
A  docs/Adding-New-Service-Guide.md
```

## 下一步

1. 运行完整测试套件确保没有破坏现有功能
2. 构建 Debian 包并在测试环境验证
3. 更新 sonic-buildimage 集成配置
4. 提交 PR 到 sonic-host-services 仓库

## 相关文件

| 文件 | 说明 |
|------|------|
| `scripts/console-monitor` | 主程序入口 |
| `tests/console_monitor/console_monitor_test.py` | 单元测试 |
| `data/debian/*.console-monitor*.service` | systemd 服务配置 |
| `docs/Adding-New-Service-Guide.md` | 集成指南 |

---
**集成完成时间**: 2026-01-18
