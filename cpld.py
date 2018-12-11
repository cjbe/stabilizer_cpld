from migen.build.generic_platform import *
from migen.build.xilinx import XilinxPlatform
from migen.build.xilinx.ise import XilinxISEToolchain

_io = [
        ("clk", 0, Pins("P43")), # MCO_2 clk from CPU

        # "spi" are the buses from the CPU
        ("spi", 0, # SPI1R on schematic
            Subsignal("mosi", Pins("P1")),
            Subsignal("miso", Pins("P2")),
            Subsignal("nss", Pins("P3")),
            Subsignal("clk", Pins("P5"))),

        ("spi", 1, # SPI2R on schematic
            Subsignal("mosi", Pins("P40")),
            Subsignal("miso", Pins("P39")),
            Subsignal("nss", Pins("P20")),
            Subsignal("clk", Pins("P19"))),

        ("spi", 2, # SPI4R on schematic
            Subsignal("mosi", Pins("P14")),
            Subsignal("miso", Pins("P13")),
            Subsignal("nss", Pins("P12")),
            Subsignal("clk", Pins("P8"))),

        ("spi", 3, # SPI5R on schematic
            Subsignal("mosi", Pins("P40")),
            Subsignal("miso", Pins("P44")),
            Subsignal("nss", Pins("P41")),
            Subsignal("clk", Pins("P42"))),


        ("adc", 0, # SPI1 on schematic
            Subsignal("miso", Pins("P27")),
            Subsignal("nss", Pins("P28")),
            Subsignal("clk", Pins("P29"))),

        ("adc", 1, # SPI5 on schematic
            Subsignal("miso", Pins("P23")),
            Subsignal("nss", Pins("P21")),
            Subsignal("clk", Pins("P22"))),


        ("dac", 0, # SPI2 on schematic
            Subsignal("mosi", Pins("P32")),
            Subsignal("nss", Pins("P30")),
            Subsignal("clk", Pins("P31")),
            Subsignal("ldac", Pins("P33"))),

        ("dac", 1, # SPI4 on schematic
            Subsignal("mosi", Pins("P37")),
            Subsignal("nss", Pins("P36")),
            Subsignal("clk", Pins("P34")),
            Subsignal("ldac", Pins("P38"))),

        ("misc", 0, Pins("P6")), # DAC0R_LDACn on schematic
        ("misc", 1, Pins("P16")),# DAC1R_LDACn on schematic
]


class Platform(XilinxPlatform):
    def __init__(self):
        XilinxPlatform.__init__(self, "xc2c32a-6-vq44", _io)
        self.toolchain.xst_opt = "-ifmt MIXED"
        self.toolchain.par_opt = ("-optimize speed -unused pullup "
                "-iostd LVCMOS33")