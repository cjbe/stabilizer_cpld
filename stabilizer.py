from migen import *
from math import ceil

# Stolen from https://github.com/quartiq/urukul
class SR(Module):
    """
    Shift register, SPI slave
    * CPOL = 0 (clock idle low during ~SEL)
    * CPHA = 0 (sample on first edge, shift on second)
    * SPI mode 0
    * samples SDI on rising clock edges (SCK1 domain)
    * shifts out SDO on falling clock edges (SCK0 domain)
    * MSB first
    * the first output bit (MSB) is undefined
    * the first output bit is available from the start of the SEL cycle until
      the first falling edge
    * the first input bit is sampled on the first rising edge
    * on the first rising edge with SEL assered, the parallel data DO
      is loaded into the shift register
    * following at least one rising clock edge, on the deassertion of SEL,
      the shift register is loaded into the parallel data register DI
    """
    def __init__(self, width):
        self.sdi = Signal()
        self.sdo = Signal()
        self.sel = Signal()

        self.di = Signal(width)
        self.do = Signal(width)

        # # #

        sr = Signal(width)

        self.clock_domains.cd_le = ClockDomain("le", reset_less=True)
        self.specials += Instance("FDPE", p_INIT=1,
                i_D=0, i_C=ClockSignal("sck1"), i_CE=self.sel, i_PRE=~self.sel,
                o_Q=self.cd_le.clk)

        self.sync.sck0 += [
                If(self.sel,
                    self.sdo.eq(sr[-1]),
                )
        ]
        self.sync.sck1 += [
                If(self.sel,
                    sr[0].eq(self.sdi),
                    If(self.cd_le.clk,
                        sr[1:].eq(self.do[:-1])
                    ).Else(
                        sr[1:].eq(sr[:-1])
                    )
                )
        ]
        self.sync.le += [
                self.di.eq(sr)
        ]



class Stabilizer(Module):
    """
    This CPLD generates the ADC conversion clock (via the ADC chip select), and
    provides the SPI clock to read out the ADC. This SPI clock and data is then
    forwarded to the CPU, which acts as a slave.

    This conversion / readout cycle runs at a repetition rate written into the
    CPLD by an SPI bus.

    This allows the ADC to be repeatedly sampled without the CPU being involved
    until it receives the "SPI read complete" interrupt.


    Hardware interface
    ------------------

    clk is driven at 128 MHz by the CPU (which runs at 128 MHz * 3 = 384 MHz)

    spi0 and spi1 are mastered by the CPU, and connect to the DACs via this CPLD.
    spi2 and spi3 are mastered by the CPLD, and connect to the CPU as a slave.

    spi0 can also be used to access a control register in the CPLD, used to
    program the ADC sample rate. The chip-select for this is misc0 line.
    """
    def __init__(self, platform):
        clk = platform.request("clk")

        spis = [platform.request("spi", i) for i in range(4)]
        adcs = [platform.request("adc", i) for i in range(2)]
        dacs = [platform.request("dac", i) for i in range(2)]

        self.clock_domains.cd_sys = ClockDomain("sys", reset_less=True)
        self.clock_domains.cd_sck0 = ClockDomain("sck0", reset_less=True)
        self.clock_domains.cd_sck1 = ClockDomain("sck1", reset_less=True)

        T_CLK = 1e3/128 # 1/(128 MHz)
        platform.add_period_constraint(clk, T_CLK)

        self.specials += [
                Instance("BUFG", i_I=clk, o_O=self.cd_sys.clk),
                Instance("BUFG", i_I=spis[0].clk, o_O=self.cd_sck1.clk),
        ]


        # Control shift register, connected to spi0 (with misc0 as CS)
        sr = SR(16)
        loop_max = Signal(10)
        self.submodules += sr

        self.comb += [
            sr.sel.eq(platform.request("misc",0)),
            sr.sdi.eq(spis[0].mosi),
            self.cd_sck0.clk.eq(~self.cd_sck1.clk),
            loop_max.eq(sr.do[:10])
        ]


        # Pass through spi0,1 to DACs
        self.comb += dacs[0].clk.eq(self.cd_sck1.clk), # This is probably unsound - check timing
        self.comb += dacs[1].clk.eq(spis[1].clk),
        for i in range(2):
            self.comb += [
                dacs[i].mosi.eq(spis[i].mosi),
                dacs[i].nss.eq(spis[i].nss),
            ]
            self.sync += dacs[i].ldac.eq(1)


        # ADC sampling
        fsm = FSM()
        self.submodules += fsm
        i = Signal(8)
        sample_clk = Signal()

        T_CNV = ceil(220 / T_CLK)

        fsm.act("DELAY",
            NextValue(i, i-1),
            If(i==0,
                NextState("CONVERT"),
                NextValue(i, T_CNV)
            )
        )
        fsm.act("CONVERT", 
            NextValue(i, i-1),
            If(i==0,
                NextState("READOUT"),
                NextValue(i, 32)
            )
        )
        fsm.act("READOUT",
            NextValue(i, i-1),
            sample_clk.eq(i[0] == 1),
            If(i==0,
                NextState("DELAY"),
                NextValue(i, loop_max)
            )
        )

        for i in range(2):
            self.sync += [
                adcs[i].nss.eq(~(fsm.ongoing("CONVERT") | fsm.ongoing("READOUT"))),
                adcs[i].clk.eq(sample_clk),
                spis[2+i].nss.eq(~fsm.ongoing("READOUT")),
                spis[2+i].clk.eq(sample_clk),
                spis[2+i].mosi.eq(adcs[i].miso),
            ]