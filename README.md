# ToyCarController

## Materials
- A laptop (with ubuntu OS)
- A Raspberry Pi 3 Board with power cable
- A MicroSD card
- A MicroSD to USB converter

and a working space with wifi access.

## How to build

### Step 1: Initialize a remotely developable Raspberry Pi 3 Board

1) Run Command: on the laptop, turn on the terminal, and type, then type enter:

   ```bash
   snap install rpi-imager 
   ```

2) Plug In: plug in the MicroSD card to the laptop
   ```bash
   # Action: plug-in: MicroSD -> Laptop  # may need converter
   ```
   
3) Run Program:

    ```bash
   # Action: Open the **Raspberry Pi imager** App.
   # Action: Select the proper settings on the UI. (trivial)
   # Action: Click run and wait it finished.
   ```

3) Run Command:
   
    ```bash
    # navigate to the root of the MicroSD card
    cd /media/congyu/bootfs
    touch ssh
    nano wpa_supplicant.conf
   ```

4) Type In: type the following content and save.
   
```bash
            country=YOUR_CONTRY_CODE  # eg. US
            ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
            update_config=1

            network={
                ssid="your wifi ssid"
                psk="your wifi password"
                key_mgmt=WPA-PSK
            }
```

5) Plug In: 
   ```bash
   # Action: plug-out: MicroSD <- Laptop
   # Action: plug-in:  MicroSD -> Raspberry Pi 3 Board
   # Action: plug-in:  Power cable -> Raspberry Pi 3 Board
   
   # Action: wait ~10 minutes (for raspberry to setup automatically)
   ```

### Step 2: Test the remote access.

1) Run Command:

    ```bash
    # locate the IP of the rasberry PI. run: 
    nmap -sn 192.168.1.0/24
    ```

2) Observe:

    ```bash
    # Action: Figure out your Rasberry IP. (eg. 192.168.1.xxx)
    ```
   
3) Run Command:

   ```bash
   ssh pi@192.168.1.xxx
   # for password, type in: raspberry
   ```

3) Run Command:

   ```bash
   exit
   ```
   
### Step 3: Setup environment and Clone the repository to the Raspberry Pi

1) Run Command:

   ```bash
   ssh pi@192.168.1.xxx
   # for password, type in: raspberry  
   ```

2) Run Command:
   
   ```bash
   sudo apt install python3-venv
   python3 -m venv toy_car_controller
   source toy_car_controller/bin/activate
   ```

2) Run Command:
   
   ```bash
   git clone <this git repository>
   cd ToyCarController
   pip3 install -r requirements.txt
   ```
   
### Step 4: Install Servo

1) Plug In:
   
   ```bash
   # Action: plug-out: Power cable <- Raspberry Pi 3 Board
   # Action: plug-in:  Adafruit Control Board -> Raspberry Pi 3 Board
   # Action: plug-in:  Servo -> Adafruit Control Board
   # Action: plug-in:  Power cable -> Adafruit Control Board
   # Action: plug-in:  Power cable -> Raspberry Pi 3 Board
   
   # Action: wait ~3 minutes (for raspberry to start)
   ```

### Step 5: Play

1) Run Command:

   ```bash
   # you might need to re-connect the resberry board
   ssh pi@192.168.1.xxx
   # for password, type in: raspberry  
   ```

   ```bash
   source toy_car_controller/bin/activate
   cd ToyCarController
   python controller.py
   ```

2) Run Program:

   ```bash
   # Action: open a **browser** (from only device under same wifi)
   # Action: go to 'http://192.168.1.xxx:5000'
   ```
