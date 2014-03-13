h100
====

Software for the Horizon H-100 Fuel Cell Stack.

Requires PiFace Digital IO

Software required can be installed using this line:
```
sudo apt-get install python{,3}-pifacedigitalio python{,3}-pifacecad python-pip python-virtualenv python-smbus python-serial
```

Enable SPI & I2C & serial
```
sudo nano /etc/modprobe.d/raspi-blacklist.conf
% comment out spi & i2c lines with a '#'
```

```
sudo nano /etc/inittab

% Comment out using '#' (last line?):
#T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100
```

```
sudo nano /boot/cmdline.txt

% Delete the two ttyAMA0 references to leave:
dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait
```

The use this command to stop you needing sudo for talking to i2c devices
```
sudo usermod -aG i2c pi
```


More project information at:

http://www.element14.com/community/community/raspberry-pi/raspberrypi_projects/blog/2013/12/02/hydrogen-fuel-cells

and

http://diydrones.com/profile/SimonHowroyd
