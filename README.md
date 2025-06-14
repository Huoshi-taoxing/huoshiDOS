# 火狮 HUOSHI - DoS 网络安全压力测试工具

**版本：v1.1.0**

> ⚠️ **仅供授权安全测试使用，禁止非法用途！**

`火狮 HUOSHI` 是一个图形化界面的网络压力测试工具，支持 TCP、UDP、HTTP 和 DNS 四种攻击类型，旨在帮助安全研究人员对授权服务器进行 DoS（拒绝服务）模拟测试，从而观察抗压能力、性能瓶颈与安全机制。

---

## 📦 功能特点

- ✅ 支持四类 DoS 测试类型：`TCP`、`UDP`、`HTTP`、`DNS`
- 带有终端命令行，支持 `nslookup` 和 `ip addr show` 等网络查询
- 实时统计发包数与失败数
- 支持深色与浅色终端配色切换
- 多线程攻击机制
- 支持暂停/恢复/停止攻击
- 免责声明与使用提示集成
- 可自定义目标 IP、端口、线程数、发包数、最大包数
- 图形界面使用 `tkinter` 
---

## 工具界面预览

（建议插入运行截图）

---

## 使用说明

1. **填写目标信息**
   - IP、端口、线程数、发包量、最大包数等

2. **选择攻击类型**
   - TCP、UDP、HTTP 或 DNS

3. **点击 ▶ 开始攻击**

4. **可使用终端命令行：**
   - `sudo nslookup https://example.com`：获取目标域名对应 IP
   - `sudo ip addr show`：查看本地主机名、内外网 IP 地址

---

## 示例命令

```plaintext
sudo nslookup https://example.com
sudo ip addr show
