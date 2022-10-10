import logging
from smbus2 import SMBus, i2c_msg
from bitstruct import CompiledFormatDict

logger = logging.getLogger(__name__)

class TLV493D:

    ADDRESS = 0x5e
    FLUX_COEF = 0.098
    TEMP_COEF = 1.1
    TEMP_OFFSET = 340

    VALUES_FMT = CompiledFormatDict(">u8u8u8 u4u2u2 u4u4 u1u1u1u1u4 u8u8u8u8",
                                    ["Bx", "By", "Bz",
                                     "TempH", "FRM", "CH",
                                     "BxH", "ByH",
                                     "Res", "T", "FF", "PD", "BzH",
                                     "Temp", "FactSet1", "FactSet2", "FactSet3"])

    CONFIG_FMT = CompiledFormatDict(">u1u2u2u1u1u1 u8 u1u1u1u5",
                                    ["P", "IICAddr", "Res1", "INT", "FAST", "LOW",
                                     "Res2", "T", "LP", "PT", "Res3"])

    def __init__(self, bus, address=ADDRESS):
        self._bus = bus if isinstance(bus, SMBus) else SMBus(bus)
        self._address = address

        self.update_data()
        self._config = {
            "P": 1,
            "IICAddr": 0,
            "INT": 0,
            "FAST": 0,
            "LOW": 0,
            "T": 0,
            "LP": 0,
            "PT": 1,
            "Res1": (self._values["FactSet1"] >> 3) & 0x03,
            "Res2": self._values["FactSet2"],
            "Res3": self._values["FactSet3"] & 0x0F
        }

    @staticmethod
    def parity(value):
        value = value ^ (value >> 4)
        value = value ^ (value >> 2)
        value = value ^ (value >> 1)
        return value & 0x01

    def get_value(self, name):
        value = self._values[name] | (self._values.get(f"{name}H", 0) << 8)
        if value & 0x0800:
            value = (value & 0x7FF) - 2048
        return value

    def get_x(self):
        return self._values["BxV"]

    def get_y(self):
        return self._values["ByV"]

    def get_z(self):
        return self._values["BzV"]

    def get_temp(self):
        return self._values["TempV"]

    x = property(get_x)
    y = property(get_y)
    z = property(get_z)
    temp = property(get_temp)

    def update_data(self):
        data = self._bus.read_i2c_block_data(self._address, 0, 10)
        self._values = self.VALUES_FMT.unpack(bytes(data))
        logger.debug("Values (raw): %s", " ".join(f"{v:02x}" for v in data))
        logger.debug("Values: %s", str(self._values))

        self._values["BxV"] = self.get_value("Bx") * self.FLUX_COEF
        self._values["ByV"] = self.get_value("By") * self.FLUX_COEF
        self._values["BzV"] = self.get_value("Bz") * self.FLUX_COEF
        self._values["TempV"] = (self.get_value("Temp") - self.TEMP_OFFSET) * self.TEMP_COEF + 25
        logger.debug("Frame %u: (%g,%g,%g) @ %g °C",
                     self._values["FRM"], self._values["BxV"],
                     self._values["ByV"], self._values["BzV"], self._values["TempV"])

    def update_config(self, **kwargs):
        self._config.update(kwargs)
        self._config["P"] = 1
        self._config["P"] = sum(map(self.parity, self._config.values())) & 0x01
        data = list(self.CONFIG_FMT.pack(self._config))
        logger.debug("Config: %s", str(self._config))
        logger.debug("Config (raw): %s", " ".join(f"{v:02x}" for v in data))
        self._bus.write_i2c_block_data(self._address, 0, data)

    def reset(self):
        logger.debug("Reset")
        self._bus.i2c_rdwr(i2c_msg.write(0, []))
