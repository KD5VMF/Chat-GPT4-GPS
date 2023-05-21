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
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import serial
import pynmea2
import serial.tools.list_ports
import pytz
from datetime import datetime, timedelta
import configparser

class Application(tk.Frame):
    def __init__(self, master=None, port=None, baudrate=9600):
        super().__init__(master)
        self.master = master
        self.grid()

        self.default_font = ("Helvetica", 12, "bold")
        self.speed_font = ("Helvetica", 24, "bold")
        self.speed_label = tk.Label(self, font=self.speed_font)
        self.altitude_label = tk.Label(self, font=self.default_font)
        self.latitude_label = tk.Label(self, font=self.default_font)
        self.longitude_label = tk.Label(self, font=self.default_font)
        self.satellites_label = tk.Label(self, font=self.default_font)
        self.time_label = tk.Label(self, font=self.default_font)
        self.date_label = tk.Label(self, font=self.default_font)

        self.speed_label.grid(row=0, column=0)
        self.altitude_label.grid(row=1, column=0)
        self.latitude_label.grid(row=2, column=0)
        self.longitude_label.grid(row=3, column=0)
        self.satellites_label.grid(row=4, column=0)
        self.time_label.grid(row=5, column=0)
        self.date_label.grid(row=6, column=0)

        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.ax = self.figure.add_subplot(111, polar=True)
        self.ax.set_yticklabels([])
        labels = [f"{degree}°\n{direction}" for degree, direction in zip(range(0, 360, 45), ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])]
        self.ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
        self.ax.set_xticklabels(labels)
        self.ax.set_theta_zero_location("N")
        self.ax.set_theta_direction(-1)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas.get_tk_widget().grid(row=7, column=0)
        self.compass_arrow, = self.ax.plot([0, 0], [0, 1], color='red')

        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.config.read(self.config_file)
        timezone = self.config.get('DEFAULT', 'TimeZone', fallback='UTC')

        self.time_zone_var = tk.StringVar()
        self.time_zone_var.set(timezone)

        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar)
        menu_bar.add_cascade(label="File", menu=file_menu)

        time_zone_menu = tk.Menu(file_menu)
        file_menu.add_cascade(label="Time Zone", menu=time_zone_menu)
        for zone in pytz.all_timezones:
            time_zone_menu.add_radiobutton(label=zone, variable=self.time_zone_var, command=self.save_time_zone)


        self.ser = serial.Serial(port, baudrate)
        self.update_labels()

        self.master.update()
        self.master.resizable(False, False)

    def save_time_zone(self):
        self.config['DEFAULT'] = {'TimeZone': self.time_zone_var.get()}
        with open(self.config_file, 'w') as cfgfile:
            self.config.write(cfgfile)

    def update_labels(self):
        valid_data = False
        while self.ser.in_waiting:
            line = self.ser.readline().decode('utf-8').rstrip()
            try:
                msg = pynmea2.parse(line)
                if isinstance(msg, pynmea2.types.talker.GGA):
                    self.latitude_label["text"] = f"Latitude: {msg.latitude:.3f}"
                    self.longitude_label["text"] = f"Longitude: {msg.longitude:.3f}"
                    if msg.altitude is not None:
                        altitude_feet = msg.altitude * 3.28084
                        self.altitude_label["text"] = f"Altitude: {altitude_feet:.3f} ft"
                    self.satellites_label["text"] = f"Number of satellites: {msg.num_sats}"
                    valid_data = True
                elif isinstance(msg, pynmea2.types.talker.RMC):
                    if msg.spd_over_grnd is not None:
                        speed_mph = msg.spd_over_grnd * 1.15078
                        self.speed_label["text"] = f"Speed: {speed_mph:.3f} mph"
                    if msg.timestamp is not None and msg.datestamp is not None:
                        datetime_obj = datetime.combine(msg.datestamp, msg.timestamp)
                        timezone = pytz.timezone(self.time_zone_var.get())
                        datetime_obj = datetime_obj.replace(tzinfo=pytz.UTC).astimezone(timezone)
                        self.time_label["text"] = f"Time: {datetime_obj.time()}"
                        self.date_label["text"] = f"Date: {datetime_obj.date()}"
                    if msg.true_course is not None:
                        heading_radians = np.deg2rad(msg.true_course)
                        self.compass_arrow.set_xdata([heading_radians, heading_radians])
                        self.figure.canvas.draw()
                    valid_data = True
            except pynmea2.ParseError:
                print(f"Parse error with line: {line}")
        if not valid_data:
            searching_text = "Searching for GPS..."
            self.speed_label["text"] = searching_text
            self.altitude_label["text"] = searching_text
            self.latitude_label["text"] = searching_text
            self.longitude_label["text"] = searching_text
            self.satellites_label["text"] = searching_text
            self.time_label["text"] = searching_text
            self.date_label["text"] = searching_text

        self.master.after(1000, self.update_labels)


def main():
    print("Available ports:")
    ports = serial.tools.list_ports.comports()
    for i, port in enumerate(ports, start=1):
        print(f"{i}: {port.device}")
    port_index = int(input("Select the port number: ")) - 1
    port = ports[port_index].device
    baudrate = int(input("Enter the baudrate: "))
    root = tk.Tk()
    root.geometry("500x680")
    root.title("GPT4-GPS")
    app = Application(master=root, port=port, baudrate=baudrate)
    app.mainloop()


if __name__ == "__main__":
    main()
