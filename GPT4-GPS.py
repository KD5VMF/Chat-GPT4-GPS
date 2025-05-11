"""
GPS Compass GUI Application

This Python script creates a GUI application to display GPS data obtained from a serial port in real-time. The application uses the Tkinter library for GUI elements and matplotlib to draw a compass. 
It utilizes the pynmea2 library to parse NMEA sentences (standard GPS data format), and PySerial to read data from the serial port. 

The data displayed includes:
- Speed (in mph)
- Altitude (in feet)
- Latitude (in degrees)
- Longitude (in degrees)
- Number of satellites in view
- Current time and date in the chosen time zone
- True course as a compass

The application updates every second to reflect real-time GPS data. In addition, it includes error handling to display a message if it is currently searching for a GPS signal.
This script also includes a dropdown menu that allows the user to select their desired time zone for time and date display. 
The chosen time zone is saved in a configuration file named 'config.ini', and this setting is loaded on startup.

To use this script, the user must input the serial port's number and baud rate when prompted in the command line. The application will then start with the main GUI window.

Notes:
- The application's window size is set to fit the compass image, and it's not resizable.
- For the compass, North is set at the top (0 or 360 degrees) and angles increase in the clockwise direction.

This script is created and maintained by OpenAI's ChatGPT. For any bugs or improvements, please report to OpenAI.
"""

import tkinter as tk
import serial
import serial.tools.list_ports
import pynmea2
import threading
from datetime import datetime
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class RetroGPSApp:
    def __init__(self, root, port, baudrate):
        self.root = root
        self.root.title("Retro GPS Monitor")
        self.root.configure(bg="black")
        self.fullscreen = True
        self.root.attributes('-fullscreen', True)
        self.root.bind("<F8>", self.toggle_fullscreen)
        self.root.bind("<q>", lambda e: self.quit())
        self.root.bind("<Q>", lambda e: self.quit())

        # Get screen size
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Layout frames
        main_frame = tk.Frame(root, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame, bg="black")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(main_frame, bg="black")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        # Retro-style canvas
        self.canvas = tk.Canvas(left_frame, bg="black", highlightthickness=0,
                                width=self.screen_width // 2, height=self.screen_height)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Radar-style compass
        self.figure = Figure(figsize=(4, 4), dpi=100, facecolor='black')
        self.ax = self.figure.add_subplot(111, polar=True)
        self.ax.set_facecolor("black")
        self.ax.tick_params(colors='lime')
        self.ax.set_yticklabels([])
        self.ax.set_theta_zero_location("N")
        self.ax.set_theta_direction(-1)
        self.ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
        self.ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], color='lime', fontsize=14)
        self.arrow, = self.ax.plot([0, 0], [0, 1], color='lime', linewidth=2)

        self.canvas_compass = FigureCanvasTkAgg(self.figure, master=right_frame)
        self.canvas_compass.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # GPS data fields
        self.text_items = {}
        self.labels = [
            "Latitude", "Longitude", "Altitude (m)", "Altitude (ft)",
            "Speed (mph)", "Speed (knots)", "Speed (km/h)",
            "True Course", "Fix Quality", "HDOP", "Satellites",
            "UTC Time", "Date"
        ]

        for i, label in enumerate(self.labels):
            y = 40 + i * 40
            self.canvas.create_text(60, y, anchor='w', text=label + ":",
                                    font=("Courier", 20, "bold"), fill="lime")
            self.text_items[label] = self.canvas.create_text(
                420, y, anchor='w', font=("Courier", 20), fill="lime", text="--")

        # Bottom dynamic placement for speed and heading
        self.large_speed_text = self.canvas.create_text(
            60, self.screen_height - 100, anchor='sw',
            font=("Courier", 40, "bold"), fill="lime", text="Speed: -- MPH"
        )
        self.heading_text = self.canvas.create_text(
            60, self.screen_height - 40, anchor='sw',
            font=("Courier", 32, "bold"), fill="lime", text="Heading: --"
        )

        # Serial read thread
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self.update_gps)
            self.thread.daemon = True
            self.thread.start()
        except Exception as e:
            self.canvas.create_text(60, 800, anchor='w', fill="red",
                                    font=("Courier", 20),
                                    text=f"Error: {e}")

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)

    def quit(self):
        self.running = False
        self.root.destroy()

    def get_compass_direction(self, angle):
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        idx = int((angle + 22.5) % 360 // 45)
        return directions[idx]

    def update_gps(self):
        while self.running:
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
                msg = pynmea2.parse(line)

                if isinstance(msg, pynmea2.types.talker.GGA):
                    self.set_text("Latitude", f"{msg.lat} {msg.lat_dir}")
                    self.set_text("Longitude", f"{msg.lon} {msg.lon_dir}")
                    self.set_text("Altitude (m)", f"{msg.altitude}")
                    try:
                        altitude_ft = float(msg.altitude) * 3.28084
                        self.set_text("Altitude (ft)", f"{altitude_ft:.2f}")
                    except:
                        self.set_text("Altitude (ft)", "--")
                    self.set_text("Fix Quality", msg.gps_qual)
                    self.set_text("HDOP", msg.horizontal_dil)
                    self.set_text("Satellites", msg.num_sats)

                elif isinstance(msg, pynmea2.types.talker.RMC):
                    speed_mph = "--"
                    try:
                        speed_knots = float(msg.spd_over_grnd)
                        speed_mph = speed_knots * 1.15078
                        self.set_text("Speed (knots)", f"{speed_knots:.2f}")
                        self.set_text("Speed (mph)", f"{speed_mph:.2f}")
                        self.set_text("Speed (km/h)", f"{speed_knots * 1.852:.2f}")
                        self.canvas.itemconfig(self.large_speed_text, text=f"Speed: {speed_mph:.1f} MPH")
                    except:
                        self.canvas.itemconfig(self.large_speed_text, text="Speed: -- MPH")

                    if msg.true_course:
                        angle = float(msg.true_course)
                        self.set_text("True Course", msg.true_course)
                        self.canvas.itemconfig(self.heading_text, text=f"Heading: {self.get_compass_direction(angle)}")
                        rad = np.deg2rad(angle)
                        self.arrow.set_xdata([0, rad])
                        self.arrow.set_ydata([0, 1])
                        self.figure.canvas.draw()

                    if msg.datestamp and msg.timestamp:
                        dt = datetime.combine(msg.datestamp, msg.timestamp)
                        self.set_text("UTC Time", dt.strftime("%H:%M:%S"))
                        self.set_text("Date", dt.strftime("%Y-%m-%d"))

            except Exception:
                continue

    def set_text(self, label, value):
        self.canvas.itemconfig(self.text_items[label], text=value)

def list_ports():
    ports = serial.tools.list_ports.comports()
    return [p for p in ports if "USB" in p.description or "Serial" in p.description]

def main():
    print("🔍 Scanning for GPS devices...\n")
    ports = list_ports()
    if not ports:
        print("❌ No compatible GPS devices found.")
        return

    for i, port in enumerate(ports, 1):
        print(f"{i}: {port.device} — {port.description}")

    try:
        port_index = int(input("\nEnter port number: ")) - 1
        port = ports[port_index].device
    except:
        print("Invalid selection.")
        return

    try:
        baudrate = int(input("Enter baudrate (default 9600): ") or "9600")
    except:
        baudrate = 9600

    root = tk.Tk()
    app = RetroGPSApp(root, port, baudrate)
    root.mainloop()

if __name__ == "__main__":
    main()
