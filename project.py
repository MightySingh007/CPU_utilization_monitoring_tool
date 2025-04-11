import psutil
import time
from pynput import keyboard
from threading import Thread
import tkinter as tk
from tkinter import scrolledtext, font
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

# Global Data Stores
keystrokes = []
cpu_history = []
mem_history = []
disk_history = []

# --- Monitoring Functions ---

def monitor_cpu(ax, canvas, label_cores, label_load):
    while True:
        cpu = psutil.cpu_percent(interval=1)
        if len(cpu_history) > 60:
            cpu_history.pop(0)
        cpu_history.append(cpu)

        ax.clear()
        ax.plot(cpu_history, label='CPU %', color='cyan')
        ax.set_ylim(0, 100)
        ax.set_title("CPU Usage")
        ax.legend()
        canvas.draw()

        # Update core usage and load average
        core_usages = psutil.cpu_percent(interval=1, percpu=True)
        label_cores.config(text=f"Core Usage: {core_usages}")
        load_avg = psutil.getloadavg()
        label_load.config(text=f"Load Averages: 1m={load_avg[0]:.2f}, 5m={load_avg[1]:.2f}, 15m={load_avg[2]:.2f}")

def monitor_memory(ax, canvas):
    while True:
        mem = psutil.virtual_memory().percent
        if len(mem_history) > 60:
            mem_history.pop(0)
        mem_history.append(mem)

        ax.clear()
        ax.plot(mem_history, label='Memory %', color='magenta')
        ax.set_ylim(0, 100)
        ax.set_title("Memory Usage")
        ax.legend()
        canvas.draw()
        time.sleep(1)

def monitor_disk(ax, canvas):
    while True:
        disk = psutil.disk_usage('/').percent
        if len(disk_history) > 60:
            disk_history.pop(0)
        disk_history.append(disk)

        ax.clear()
        ax.plot(disk_history, label='Disk %', color='orange')
        ax.set_ylim(0, 100)
        ax.set_title("Disk Usage")
        ax.legend()
        canvas.draw()
        time.sleep(1)

def monitor_network(text_widget):
    while True:
        connections = psutil.net_connections(kind='inet')
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, "Network Connections:\n")
        for conn in connections:
            laddr = conn.laddr
            raddr = conn.raddr if conn.raddr else "N/A"
            status = conn.status
            text_widget.insert(tk.END, f"{laddr} → {raddr} | Status: {status}\n")
        time.sleep(5)

def on_press(key):
    try:
        keystrokes.append(key.char)
    except AttributeError:
        keystrokes.append(str(key))

def start_keylogger(text_widget):
    with keyboard.Listener(on_press=on_press) as listener:
        while True:
            if keystrokes:
                text_widget.insert(tk.END, ''.join(keystrokes))
                keystrokes.clear()
            time.sleep(1)

def monitor_processes(text_widget):
    while True:
        processes = [(p.info['pid'], p.info['name'], p.info['cpu_percent']) 
                     for p in psutil.process_iter(['pid', 'name', 'cpu_percent'])]
        processes.sort(key=lambda x: x[2], reverse=True)
        top = processes[:10]

        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, "Top CPU Consuming Processes:\n")
        for pid, name, cpu in top:
            text_widget.insert(tk.END, f"PID: {pid} | {name} | CPU: {cpu}%\n")
        time.sleep(3)

# --- GUI Creation ---

def create_gui():
    window = tk.Tk()
    window.title("Full Task Manager with Charts")
    window.geometry("1000x800")
    window.configure(bg="#1E1E1E")

    header_font = font.Font(family="Arial", size=14, weight="bold")
    text_font = font.Font(family="Courier", size=10)

    # Scrollable Frame
    canvas = tk.Canvas(window, bg="#1E1E1E")
    scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="#1E1E1E")

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # --- Charts and Info Widgets ---

    # CPU Chart
    fig_cpu, ax_cpu = plt.subplots(figsize=(8, 3), dpi=100)
    canvas_cpu = FigureCanvasTkAgg(fig_cpu, master=scroll_frame)
    canvas_cpu.get_tk_widget().pack(pady=10)

    label_cores = tk.Label(scroll_frame, font=text_font, fg="white", bg="#1E1E1E")
    label_cores.pack()
    label_load = tk.Label(scroll_frame, font=text_font, fg="white", bg="#1E1E1E")
    label_load.pack()

    # Memory Chart
    fig_mem, ax_mem = plt.subplots(figsize=(8, 3), dpi=100)
    canvas_mem = FigureCanvasTkAgg(fig_mem, master=scroll_frame)
    canvas_mem.get_tk_widget().pack(pady=10)

    # Disk Chart
    fig_disk, ax_disk = plt.subplots(figsize=(8, 3), dpi=100)
    canvas_disk = FigureCanvasTkAgg(fig_disk, master=scroll_frame)
    canvas_disk.get_tk_widget().pack(pady=10)

    # Network Info
    tk.Label(scroll_frame, text="Network Connections", font=header_font, fg="white", bg="#1E1E1E").pack(pady=(20, 5))
    text_network = scrolledtext.ScrolledText(scroll_frame, height=10, width=100, font=text_font, bg="black", fg="lime")
    text_network.pack()

    # Keylogger
    tk.Label(scroll_frame, text="Keystrokes", font=header_font, fg="white", bg="#1E1E1E").pack(pady=(20, 5))
    text_keys = scrolledtext.ScrolledText(scroll_frame, height=5, width=100, font=text_font, bg="black", fg="lime")
    text_keys.pack()

    # Process Info
    tk.Label(scroll_frame, text="Top Processes", font=header_font, fg="white", bg="#1E1E1E").pack(pady=(20, 5))
    text_procs = scrolledtext.ScrolledText(scroll_frame, height=10, width=100, font=text_font, bg="black", fg="cyan")
    text_procs.pack()

    # --- Threads ---
    Thread(target=monitor_cpu, args=(ax_cpu, canvas_cpu, label_cores, label_load), daemon=True).start()
    Thread(target=monitor_memory, args=(ax_mem, canvas_mem), daemon=True).start()
    Thread(target=monitor_disk, args=(ax_disk, canvas_disk), daemon=True).start()
    Thread(target=monitor_network, args=(text_network,), daemon=True).start()
    Thread(target=start_keylogger, args=(text_keys,), daemon=True).start()
    Thread(target=monitor_processes, args=(text_procs,), daemon=True).start()

    window.mainloop()

def main():
    print("Launching Full Task Manager UI...")
    create_gui()

if __name__ == "__main__":
    main()
