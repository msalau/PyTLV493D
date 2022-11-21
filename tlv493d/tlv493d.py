import logging
from bitstruct import CompiledFormatDict

logger = logging.getLogger(__name__)

class TLV493D:

    FLUX_COEF = 0.098
    TEMP_COEF = 1.1
    TEMP_OFFSET = 340

    VALUES_FMT = CompiledFormatDict(">u8u8u8 u4u2u2 u4u4 u1u1u1u1u4 u8u8u8u8",
                                    ["BxH", "ByH", "BzH",
                                     "TempH", "FRM", "CH",
                                     "BxL", "ByL",
                                     "Res", "T", "FF", "PD", "BzL",
                                     "TempL", "FactSet1", "FactSet2", "FactSet3"])

    CONFIG_FMT = CompiledFormatDict(">u1u2u2u1u1u1 u8 u1u1u1u5",
                                    ["P", "IICAddr", "Res1", "INT", "FAST", "LOW",
                                     "Res2", "T", "LP", "PT", "Res3"])
    DEFAULT_ADDRESS = 0x5e
    DEFAULT_CONFIG = {
        "P": 0,
        "IICAddr": 0,
        "INT": 0,
        "FAST": 0,
        "LOW": 0,
        "T": 0,
        "LP": 0,
        "PT": 1,
        "Res1": 0,
        "Res2": 0,
        "Res3": 0,
    }

    def __init__(self, bus):
        self._bus = bus
        self._address = self.DEFAULT_ADDRESS

        self.update_data()
        self._config = self.DEFAULT_CONFIG
        self._config["Res1"] = (self._values["FactSet1"] >> 3) & 0x03
        self._config["Res2"] = self._values["FactSet2"]
        self._config["Res3"] = self._values["FactSet3"] & 0x1F

    @staticmethod
    def parity(value):
        value = value ^ (value >> 4)
        value = value ^ (value >> 2)
        value = value ^ (value >> 1)
        return value & 0x01

    def get_value(self, name):
        return self._values[name]

    def get_b_value(self, name):
        value = self._values[f"{name}L"] | (self._values[f"{name}H"] << 4)
        value = (value & 0x7FF) - (value & 0x800)
        return value

    def get_temp_value(self):
        value = self._values["TempL"] | (self._values["TempH"] << 8)
        value = (value & 0x7FF) - (value & 0x800)
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

        self._values["BxV"] = self.get_b_value("Bx") * self.FLUX_COEF
        self._values["ByV"] = self.get_b_value("By") * self.FLUX_COEF
        self._values["BzV"] = self.get_b_value("Bz") * self.FLUX_COEF
        self._values["TempV"] = (self.get_temp_value() - self.TEMP_OFFSET) * self.TEMP_COEF + 25

    def update_config(self, **kwargs):
        for name, value in kwargs.items():
            if name not in self._config:
                raise KeyError(f"Invalid config parameter: {name}")
            if name.startswith("Res"):
                raise AttributeError(f"Reserved parameters should not be changed: {name}")
            self._config[name] = value
        # Calculate parity
        self._config["P"] = 1
        self._config["P"] = sum(map(self.parity, self._config.values())) & 0x01
        data = list(self.CONFIG_FMT.pack(self._config))
        logger.debug("Config: %s", str(self._config))
        logger.debug("Config (raw): %s", " ".join(f"{v:02x}" for v in data))
        self._bus.write_i2c_block_data(self._address, 0, data)
        # Update address
        self._address = self.DEFAULT_ADDRESS ^ (((self._config["IICAddr"] << 3) |
                                                 (self._config["IICAddr"] << 2)) & 0x14)
