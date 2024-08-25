# Hardware "HID Attack" to Control 2 Computers

**HARDWARE_SYSTEM_WITHOUT_BORDERS**
A hardware based approach to system without borders where you can control two computers using a single keyboard and mouse.

![ATMEGA32U4 Wiring](./images/header.png)



## What you can do with this project

With this project, you can use software on a single system and then use two physical devices to control two computers. 

This leverages HID or human interface device attack vector to wirelessly transmit keystrokes and mouse movements to another computer. 

To accomplish this, we leverage two **ATMEGA32U4**s that can act as an HID, in combination with two **NRF24L01**s to provide wireless connectivity between the two devices. 

One ATMEGA32U4 can connect to your host machine via serial and get commands from a python script we have running which receives serial communication to the main ATMEGA32U4 which in turn, sends commands to the secondary ATMEGA32U4 via wireless over the **NRF24L01** and then allows keyboard and mouse control over a secondary system. 

The best part? The secondary computer doesn't know it's being controlled remotely since it "Trusts" the USB input as a keyboard device.

## Use Cases

1. While you can use [mouse without borders from miscrosoft](https://github.com/microsoft/PowerToys) between two windows machines, you cannot as easily control windows + linux or windows + mac combinations with that. *This* will work between *any* OS.

2. Due to security constraints, you may not be able to run software for sharing mice and keyboards on certain computers without getting ***busted***. Using this project, as long as you have a single computer you can control, this will allow you to control the ***other*** safely without being caught.




## Wiring 

First make sure you pick up 2 [NRF2401](https://www.amazon.com/dp/B08R9F11D1?ref=ppx_yo2ov_dt_b_fed_asin_title)s and two [ATmega32U4](https://www.amazon.com/dp/B08CC24JRS?ref=ppx_yo2ov_dt_b_fed_asin_title)s from your preferred electronics dealer.


You'll want to wire it up. I've color corrdinated for you to make it easier to seee my pictures. 

But basically the mapping is 

```
ATmega32U4 pins --- NRF2401 pins

pin 7   --- ce (green)
pin 8   --- csn (blue)
pin 15  --- sck (purple)
pin 16  --- mosi (white)
pin 14  --- Miso (grey)

```

I really appreciate the breakout board for the NRF2401. I also have some power supply regulators since I hear that the NRF2401 is really critical to use 3.5v with but requires higher amps than an arduino or ATmega32U4 could provide. 

**Here's the ATMEGA32U4 wired up:**

![ATMEGA32U4 Wiring](./images/wired1.jpg)


**Make sure you share ground!**

Make sure you have the ATMEGA32U4 and the NRF2401 sharing grounds between the two units or else it may not know the correct baseline for the wireless signals coming in. 

![Soldering For Common Grounds](./images/wired2.jpg)

**NRF24L01 wiring**

![NRF24L01 Wiring](./images/wired3.jpg)

# Installation

Run `pip install -r requirements.txt` to install the requirements

# Running the software 

run `python app.py` to kick things off. Then, you'll notice that when you take your cursor to the right side of the screen that it will start piping commands via serial to the tx.ino arduino.

When you come back the other direction, it will turn it off. 


# Testing the communication works

To test the wireless is actually working correctly, you can install the alternative `.ino` files to test. RX on one mega and TX on the other (found in the comTests folder)





