# Chat-GPT4-GPS
GPS Program built with Chat-GPT4 to run in Python. 

This GPS Compass GUI Application is a robust, user-friendly interface designed to parse and display GPS data from a connected GPS device in real-time. It is developed in Python, utilizing several libraries to effectively process and present the GPS data.

**Key Components:**

1. **Tkinter**: The GUI framework is based on Tkinter, Python's standard GUI package. This application uses a main window frame and various labels to dynamically display GPS data.

2. **Matplotlib**: The compass component of the GUI is designed using matplotlib. A polar plot from matplotlib is embedded within the Tkinter window to display the compass, which is updated in real-time according to the GPS heading data.

3. **Numpy**: Numpy is used for mathematical operations, including radian conversion for the compass heading.

4. **Serial and Pynmea2**: These libraries are essential for establishing a connection with the GPS device and parsing the incoming NMEA 0183 (National Marine Electronics Association) data stream, respectively.

5. **Pytz and Configparser**: These libraries are used for managing timezones and user preferences. Pytz allows accurate timezone calculations, which are necessary for displaying the correct time according to the user's preference. Configparser is used to save and load the user's selected timezone, making it persistent across different program executions.

**Functionality:**

The application starts by asking the user to choose the port number and baud rate for the serial connection to the GPS device. Once the connection is established, the program continuously reads incoming data from the device.

The NMEA data is parsed into different message types, particularly GPGGA and GPRMC. These messages contain various pieces of data including latitude, longitude, altitude, speed over ground, the number of satellites, and more. The parsed data is then used to update the respective labels in the GUI.

The compass heading, derived from the GPRMC message, is displayed using a red arrow on a circular compass. The compass uses a polar plot, with North pointing upwards, and updates dynamically with the heading data.

In addition to the dynamic GPS data display, the application provides a user-friendly menu to adjust the timezone. The timezone preference is saved, ensuring it persists for subsequent uses of the application.

The application window's title is set to "GPT4-GPS", and its size is tailored to fit the contents snugly, ensuring a clean, compact, and informative interface for real-time GPS data tracking and display.

In essence, this Python script is a comprehensive and interactive tool for real-time GPS tracking, providing a user-friendly GUI for displaying GPS data, including geographical coordinates, speed, altitude, number of satellites, current time and date according to user-selected timezone, and a dynamic compass showing the current heading.
