#!/usr/bin/env python

# Author: Ilia Baranov
# Very simple demo of showing system stats on the Keyboard LCD

# import os
# import socket
import psutil
from urllib.request import urlopen
import platform

from time import strftime, time
from libs.ergodox_infinity_display import ErgodoxInterface

serial_port = 'COM3'


def main():
    IS_WINDOWS = False
    IS_MAC = False

    if 'Windows' in platform.system():
        import wmi
        IS_WINDOWS = True
        w = wmi.WMI(namespace='root\\wmi')
    elif 'Darwin' in platform.system():
        IS_MAC = True

    if not IS_MAC:
        import serial
        # TODO: Dynamically discover the serial device
        # dev/serial/by-id/usb-Kiibohd_Keyboard_-_MDErgo1_PartialMap_pjrcUSB_full_Clean_master_-_2016-02-11_22:56:25_-0800-if02
        # Change to (Serial port - 1) on Windows.
        ser = serial.Serial(serial_port, 115200, timeout=0.5)
        ser.close()
        ser.open()
    else:
        from libs.MacSerial import MacSerial
        ser = MacSerial()

    dox = ErgodoxInterface(ser)

    # Keeping track of Incoming + outgoing net traffic
    l_net = psutil.net_io_counters().bytes_recv \
        + psutil.net_io_counters().bytes_sent
    l_time = time()

    # Get external IP once (Not ideal....)
    # External IP, This may need to be fixed as website changes
    ip = urlopen('http://whatismyip.org').read()
    p = ip.find("font-weight: 600;".encode("utf-8"))
    ip = ip[p + 19:p + 34].strip('</span'.encode("utf-8"))
    ip = ip.decode("utf-8")
    # hostname = socket.gethostname()

    try:
        while True:
            if IS_WINDOWS:
                # Temp of CPU (WINDOWS ONLY, Linux needs to use sensors)
                try:
                    temp = (w.MSAcpi_ThermalZoneTemperature()[
                            0].CurrentTemperature / 10.0) - 273.15
                except BaseException:
                    print('Could not read temp, skipping')
                    temp = 22.0
            else:
                # TODO: fix temperature for linux
                temp = None

            cpu = psutil.cpu_percent(interval=None)  # CPU Usage
            mem = psutil.virtual_memory().percent  # Memory Usage
            disk = psutil.disk_usage('/').percent
            net = ((psutil.net_io_counters().bytes_recv
                    + psutil.net_io_counters().bytes_sent)
                   - l_net) / (time() - l_time)  # Messy, lousy net estimate
            l_time = time()
            l_net = psutil.net_io_counters().bytes_recv \
                + psutil.net_io_counters().bytes_sent

            dox.lcd_hex_color(0x00000C)

            dox.lcd.clear()

            # Show CPU, MEM, etc loading in bar graphs
            y_t = 24
            dox.lcd.format_string("CPU [", 0, y_t)
            dox.lcd.format_string("]", 76, y_t)
            # Represent bar graph for CPU usage (total)
            dox.lcd.format_string("" * int(round(cpu / 10)), 26, y_t)
            if temp:
                dox.lcd.format_string("{0:.0f}".format(temp) + "*C", 82, y_t)
            y_t -= 8
            dox.lcd.format_string(
                strftime("%m-%d"), 103, y_t)  # Print date and time
            dox.lcd.format_string("MEM [", 0, y_t)
            dox.lcd.format_string("]", 76, y_t)
            # Represent bar graph for Mem
            dox.lcd.format_string("" * int(round(mem / 10)), 26, y_t)
            y_t -= 8
            dox.lcd.format_string(
                strftime("%H:%M"), 103, y_t)  # Print date and time
            dox.lcd.format_string("DSK [", 0, y_t)
            dox.lcd.format_string("]", 76, y_t)
            # Represent bar graph for Disk usage
            dox.lcd.format_string("" * int(round(disk / 10)), 26, y_t)
            y_t -= 8
            dox.lcd.format_string("NET ", 0, y_t)
            dox.lcd.format_string(
                "{0:.1f}".format(
                    net / 1048576) + "M", 24, y_t)
            dox.lcd.format_string(ip.rjust(15), 53, y_t)

            dox.send()  # Update LCD all at once

    except KeyboardInterrupt:  # Press Ctrl + C to exit
        print('Exit')

    ser.close()

if __name__ == '__main__':
    main()
