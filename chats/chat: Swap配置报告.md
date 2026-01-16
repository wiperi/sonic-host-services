# Swap 配置报告

**日期**: 2026-01-14  
**目的**: 为系统添加 4G swap 空间，缓解内存压力

---

## 1. 问题背景

系统内存使用较高，需要添加 swap 空间来缓解内存压力。

初始内存状态：
```
               total        used        free      shared  buff/cache   available
Mem:           7.7Gi       5.5Gi       226Mi        31Mi       2.3Gi       2.2Gi
```

---

## 2. 遇到的问题

### 2.1 首次尝试：使用 fallocate 创建 swap 文件

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**结果**: 失败
```
swapon: /swapfile: swapon failed: Invalid argument
```

### 2.2 第二次尝试：使用 dd 创建 swap 文件

```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 status=progress
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**结果**: 同样失败
```
swapon: /swapfile: swapon failed: Invalid argument
```

### 2.3 问题分析

检查文件系统类型：
```bash
df -Th /
```

输出：
```
Filesystem     Type     Size  Used Avail Use% Mounted on
root-overlay   overlay   15G  8.5G  5.7G  60% /
```

**根本原因**: 根目录 `/` 使用的是 **overlay 文件系统**，不支持直接创建 swap 文件。

---

## 3. 解决方案

### 3.1 找到可用的物理分区

```bash
df -Th | grep -v overlay
```

输出：
```
Filesystem     Type      Size  Used Avail Use% Mounted on
/dev/mmcblk0p1 ext4       15G  8.5G  5.7G  60% /host
/dev/loop1     ext4      2.0G  633M  1.2G  35% /var/log
```

发现 `/host` 挂载在 ext4 分区上，支持 swap 文件。

### 3.2 在 /host 创建 swap 文件

```bash
# 创建 4G swap 文件
sudo dd if=/dev/zero of=/host/swapfile bs=1M count=4096 status=progress

# 设置权限
sudo chmod 600 /host/swapfile

# 格式化为 swap
sudo mkswap /host/swapfile

# 启用 swap
sudo swapon /host/swapfile
```

**结果**: 成功！

### 3.3 持久化配置

将 swap 添加到 `/etc/fstab`，确保重启后自动生效：

```bash
echo '/host/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 4. 最终结果

### 4.1 验证 swap 已启用

```bash
free -h
```

输出：
```
               total        used        free      shared  buff/cache   available
Mem:           7.7Gi       5.5Gi       226Mi        31Mi       2.3Gi       2.2Gi
Swap:          4.0Gi          0B       4.0Gi
```

### 4.2 配置摘要

| 项目 | 值 |
|------|-----|
| Swap 文件位置 | `/host/swapfile` |
| Swap 大小 | 4 GiB |
| 文件系统 | ext4 (在 /host 分区) |
| 持久化 | 已添加到 `/etc/fstab` |

---

## 5. 经验总结

1. **Overlay 文件系统不支持 swap 文件**：SONiC 等使用 overlay 根文件系统的系统，不能直接在 `/` 下创建 swap 文件。

2. **需要找到实际的物理分区**：必须在 ext4、xfs 等支持 swap 的真实文件系统上创建 swap 文件。

3. **使用 dd 而非 fallocate**：某些文件系统（如 xfs、btrfs）使用 `fallocate` 创建的文件可能无法用作 swap，推荐使用 `dd` 创建。

4. **持久化配置**：别忘了将 swap 添加到 `/etc/fstab`，否则重启后会失效。

---

## 6. 参考命令

```bash
# 查看当前内存和 swap 使用情况
free -h

# 查看 swap 详情
cat /proc/swaps

# 临时禁用 swap
sudo swapoff /host/swapfile

# 重新启用 swap
sudo swapon /host/swapfile

# 调整 swappiness（默认60，降低可减少 swap 使用）
sudo sysctl vm.swappiness=10
```
