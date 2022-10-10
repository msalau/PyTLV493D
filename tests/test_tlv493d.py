from conftest import *
from tlv493d import TLV493D
from smbus2 import SMBus, i2c_msg

def test_init_from_bus_number(smbus_mock):
    SMBus.read_i2c_block_data.return_value = list(bytes(10))
    dev = TLV493D(1)
    SMBus.open.assert_called_once_with(1)
    SMBus.read_i2c_block_data.assert_called_once_with(0x5e, 0, 10)

def test_init_from_bus_device(smbus_mock):
    SMBus.read_i2c_block_data.return_value = list(bytes(10))
    dev = TLV493D("/dev/i2c-0")
    SMBus.open.assert_called_once_with("/dev/i2c-0")
    SMBus.read_i2c_block_data.assert_called_once_with(0x5e, 0, 10)

def test_init_from_smbus_object(smbus_mock):
    SMBus.read_i2c_block_data.return_value = list(bytes(10))
    dev = TLV493D(SMBus())
    SMBus.open.assert_not_called()
    SMBus.read_i2c_block_data.assert_called_once_with(0x5e, 0, 10)

def test_init_with_address(smbus_mock):
    SMBus.read_i2c_block_data.return_value = list(bytes(10))
    dev = TLV493D(SMBus(), address=42)
    SMBus.open.assert_not_called()
    SMBus.read_i2c_block_data.assert_called_once_with(42, 0, 10)

def test_reset(smbus_mock):
    SMBus.read_i2c_block_data.return_value = list(bytes(10))
    TLV493D(SMBus()).reset()
    SMBus.i2c_rdwr.assert_called_once()

def test_read_bx_pos(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [1, 0, 0, 0, 0x20, 0, 0, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev._values["Bx"] == 1
    assert dev._values["BxH"] == 2
    assert dev.get_value("Bx") == 0x201

def test_read_bx_neg(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [1, 0, 0, 0, 0x80, 0, 0, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev._values["Bx"] == 1
    assert dev._values["BxH"] == 8
    assert dev.get_value("Bx") == -2047

def test_read_by_pos(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [0, 4, 0, 0, 0x03, 0, 0, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev._values["By"] == 4
    assert dev._values["ByH"] == 3
    assert dev.get_value("By") == 0x304

def test_read_by_neg(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [0, 0, 0, 0, 0x08, 0, 0, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev._values["By"] == 0
    assert dev._values["ByH"] == 8
    assert dev.get_value("By") == -2048

def test_read_bz_pos(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [0, 0, 8, 0, 0, 0x07, 0, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev._values["Bz"] == 8
    assert dev._values["BzH"] == 7
    assert dev.get_value("Bz") == 0x708

def test_read_bz_neg(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [0, 0, 8, 0, 0, 0x08, 0, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev._values["Bz"] == 8
    assert dev._values["BzH"] == 8
    assert dev.get_value("Bz") == -2040

def test_read_temp_pos(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [0, 0, 0, 0x70, 0, 0, 0x20, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev._values["Temp"] == 32
    assert dev._values["TempH"] == 7
    assert dev.get_value("Temp") == 0x720

def test_read_temp_neg(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [0, 0, 0, 0x80, 0, 0, 0x20, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev._values["Temp"] == 32
    assert dev._values["TempH"] == 8
    assert dev.get_value("Temp") == -2016

def test_xyz_and_temp(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [1, 2, 4, 0x10, 0, 0, 0x5e, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev.x == 0.098
    assert dev.y == 0.196
    assert dev.z == 0.392
    assert dev.temp == 36

@pytest.mark.parametrize("name, value", [("FRM", 0x0C), ("CH", 0x03)])
def test_3h(smbus_mock, name, value):
    SMBus.read_i2c_block_data.return_value = [0, 0, 0, value, 0, 0, 0, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev.get_value(name) == 3

@pytest.mark.parametrize("name, value", [("Res", 0x80), ("T", 0x40), ("FF", 0x20), ("PD", 0x10)])
def test_5h(smbus_mock, name, value):
    SMBus.read_i2c_block_data.return_value = [0, 0, 0, 0, 0, value, 0, 0, 0, 0]
    dev = TLV493D(SMBus())
    assert dev.get_value(name) == 1

def test_factory_settings(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [0, 0, 0, 0, 0, 0, 0, 1, 2, 3]
    dev = TLV493D(SMBus())
    assert dev.get_value("FactSet1") == 1
    assert dev.get_value("FactSet2") == 2
    assert dev.get_value("FactSet3") == 3

@pytest.mark.parametrize("name, value, mod1, mod2", [
    ("IICAddr", 3, 0xE0, 0),
    ("INT", 1, 0x04, 0),
    ("FAST", 1, 0x02, 0),
    ("LOW", 1, 0x01, 0),
    ("T", 1, 0, 0x80),
    ("LP", 1, 0, 0x40),
    ("PT", 1, 0, 0x20)
])
def test_config(smbus_mock, name, value, mod1, mod2):
    SMBus.read_i2c_block_data.return_value = list(bytes(10))
    dev = TLV493D(1)
    for key in dev._config:
        dev._config[key] = 0
    dev.update_config(**{name: value})
    SMBus.write_i2c_block_data(0x5e, 0, [mod1, 0, mod2])

def test_config_factory_settings(smbus_mock):
    SMBus.read_i2c_block_data.return_value = [0, 0, 0, 0, 0, 0, 0, 0x18, 0x42, 0x14]
    dev = TLV493D(SMBus())
    dev.update_config()
    SMBus.write_i2c_block_data(0x5e, 0, [0x98, 0x42, 0x14])
