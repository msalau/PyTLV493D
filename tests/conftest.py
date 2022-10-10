import pytest
import smbus2

@pytest.fixture()
def smbus_mock(mocker):
    mocker.patch("smbus2.SMBus.open")
    mocker.patch("smbus2.SMBus.close")
    mocker.patch("smbus2.SMBus.read_i2c_block_data")
    mocker.patch("smbus2.SMBus.write_i2c_block_data")
    mocker.patch("smbus2.SMBus.i2c_rdwr")
