#!/usr/bin/env python3

import argparse
import logging
import sys
import time
from smbus2 import SMBus

#pylint: disable=wrong-import-position
sys.path.append(".")
sys.path.append("..")
#pylint: enable=wrong-import-position

from tlv493d import TLV493D

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

def main():
    parser = argparse.ArgumentParser(description="TLV493D value reader")
    parser.add_argument("bus", type=int, help="I2C bus number")
    parser.add_argument("-d", "--debug", action="store_true", help="enable debug mode")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger("tlv493d").setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    logger.debug("Arguments: %s", args)

    try:
        sensor = TLV493D(SMBus(args.bus))
        sensor.update_config(FAST=1, LOW=1, INT=0)
        while True:
            time.sleep(0.2)
            sensor.update_data()
            logger.info("(%g,%g,%g) mT @ %g °C", sensor.x, sensor.y, sensor.z, sensor.temp)
    except FileNotFoundError:
        logging.error("I2C bus is not accessible")
    except KeyboardInterrupt:
        logging.debug("Stopping")

if __name__ == "__main__":
    main()
