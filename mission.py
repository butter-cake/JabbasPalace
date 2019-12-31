#!/usr/bin/env python3
# Copyright 2019 Amazon.com, Inc. or its affiliates.  All Rights Reserved.
# 
# You may not use this file except in compliance with the terms and conditions 
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMAZON SPECIFICALLY DISCLAIMS, WITH 
# RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING 
# THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.

import os
import sys
import time
import logging
import json
import random
import threading

from enum import Enum
from agt import AlexaGadget

from ev3dev2.led import Leds
from ev3dev2.sound import Sound

from ev3dev2.motor import OUTPUT_B, OUTPUT_C, MoveTank, SpeedPercent
from ev3dev2.sensor.lego import InfraredSensor, ColorSensor

# Set the logging level to INFO to see messages from AlexaGadget
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(message)s')
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger = logging.getLogger(__name__)


class Direction(Enum):
    """
    The list of directional commands and their variations.
    These variations correspond to the skill slot values.
    """
    FORWARD = ['forward', 'forwards', 'go forward']
    BACKWARD = ['back', 'backward', 'backwards', 'go backward']
    LEFT = ['left', 'go left']
    RIGHT = ['right', 'go right']
    STOP = ['stop', 'brake']


class Command(Enum):
    """
    The list of preset commands and their invocation variation.
    These variations correspond to the skill slot values.
    """
    MOVE_CIRCLE = ['circle', 'spin']
    MOVE_SQUARE = ['square']
    PATROL = ['patrol', 'guard mode', 'sentry mode']
    FIRE_ONE = ['cannon', '1 shot', 'one shot']
    FIRE_ALL = ['all shot']


class MindstormsGadget(AlexaGadget):
    """
    A Mindstorms gadget that performs movement based on voice commands.
    Two types of commands are supported, directional movement and preset.
    """

    def __init__(self):
        """
        Performs Alexa Gadget initialization routines and ev3dev resource allocation.
        """
        super().__init__()

        # Gadget state
        
        self.isDoorOpen = False
        self.verified = True

        # Ev3dev initialization
        self.leds = Leds()
        self.sound = Sound()
        self.drive = MoveTank(OUTPUT_B, OUTPUT_C)
        
        self.ir_sensor = InfraredSensor()
        self.ir_sensor.mode = self.ir_sensor.MODE_IR_REMOTE
        self.color_sensor = ColorSensor()
        self.color_sensor.mode = 'COL-COLOR' # WHITE

        # Start threads
        threading.Thread(target=self._patrol_thread, daemon=True).start()

    def on_connected(self, device_addr):
        """
        Gadget connected to the paired Echo device.
        :param device_addr: the address of the device we connected to
        """
        self.leds.set_color("LEFT", "GREEN")
        self.leds.set_color("RIGHT", "GREEN")
        logger.info("{} connected to Echo device".format(self.friendly_name))

    def on_disconnected(self, device_addr):
        """
        Gadget disconnected from the paired Echo device.
        :param device_addr: the address of the device we disconnected from
        """
        self.leds.set_color("LEFT", "BLACK")
        self.leds.set_color("RIGHT", "BLACK")
        logger.info("{} disconnected from Echo device".format(self.friendly_name))

    def on_custom_mindstorms_gadget_control(self, directive):
        """
        Handles the Custom.Mindstorms.Gadget control directive.
        :param directive: the custom directive with the matching namespace and name
        """
        try:
            payload = json.loads(directive.payload.decode("utf-8"))
            logger.info("Control payload: {}".format(payload))
            control_type = payload["type"]
            
            if control_type == "open":
                self._open()

            if control_type == "close":
                self._close()

        except KeyError:
            print("Missing expected parameters: {}".format(directive), file=sys.stderr)

    

    def _activate(self, command, speed=50):
        """
        Handles preset commands.
        :param command: the preset command
        :param speed: the speed if applicable
        """
        print("Activate command: ({}, {})".format(command, speed), file=sys.stderr)
       

    def _open(self):
        if (not self.isDoorOpen) and self.verified:
            logger.info("Open door")
            self.drive.on_for_rotations(1*SpeedPercent(10), 1*SpeedPercent(10), 1.5)
            self.isDoorOpen = True
            self.color_sensor.mode = 'COL-AMBIENT' # Blue
        else:
            self.color_sensor.mode = 'COL-REFLECT' # RED

    def _close(self):
        self.color_sensor.mode = 'COL-COLOR' # WHITE

        if self.isDoorOpen:
            logger.info("Close door")
            self.drive.on_for_rotations(-1*SpeedPercent(10), -1*SpeedPercent(10), 1.5)
            self.isDoorOpen = False

    def _patrol_thread(self):
        while True:
            while not self.isDoorOpen:
                logger.info("Patrol mode activated for checking beacon")
                distance = self.ir_sensor.distance()
                logger.info("Distance: {}".format(distance))

                if distance is not None and distance < 100:
                    self.verified = True
                    logger.info("Beacon found")
                else:
                    self.verified = False
                time.sleep(1)

            time.sleep(1)

if __name__ == '__main__':

    gadget = MindstormsGadget()

    # Set LCD font and turn off blinking LEDs
    os.system('setfont Lat7-Terminus12x6')
    gadget.leds.set_color("LEFT", "BLACK")
    gadget.leds.set_color("RIGHT", "BLACK")

    # Startup sequence
    gadget.sound.play_song((('C4', 'e'), ('D4', 'e'), ('E5', 'q')))
    gadget.leds.set_color("LEFT", "GREEN")
    gadget.leds.set_color("RIGHT", "GREEN")

    # Gadget main entry point
    gadget.main()

    # Shutdown sequence
    gadget.sound.play_song((('E5', 'e'), ('C4', 'e')))
    gadget.leds.set_color("LEFT", "BLACK")
    gadget.leds.set_color("RIGHT", "BLACK")
