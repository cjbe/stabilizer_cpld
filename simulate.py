from collections import namedtuple

from migen import *
from migen.fhdl.specials import Tristate
from migen.build.generic_platform import ConstraintError

from stabilizer import Stabilizer
from cpld import Platform


class SimTristate:
    @staticmethod
    def lower(dr):
        return SimTristateImpl(dr.i, dr.o, dr.oe, dr.target)


class SimTristateImpl(Module):
    def __init__(self, i, o, oe, target):
        self.i = i
        self.o = o
        self.oe = oe
        self.target = target
        self.comb += [
                # If(oe, target.eq(o)),
                # i.eq(Mux(oe, o, target))
                i.eq(target)
        ]


class SimInstance:
    @staticmethod
    def lower(dr):
        return Module()


class TB(Module):
    def __init__(self, platform, dut):
        self.platform = platform
        self.submodules.dut = CEInserter(["le"])(dut)
        for k in "clk spi adc dac misc".split():
            v = []
            while True:
                try:
                    v.append(platform.lookup_request(k, len(v)))
                except ConstraintError:
                    break
            if len(v) == 1:
                v = v[0]
            setattr(self, k, v)

    def spi(self, ):
        # while (yield self.dut.cd_sck0.clk):
        #     pass
        yield self.cs.eq(cs)
        miso = 0
        for i in range(n - 1, -1, -1):
            yield self.eem[1].io.eq((mosi >> i) & 1)
            yield self.eem[0].io.eq(0)
            yield
            yield self.eem[0].io.eq(1)
            miso = (miso << 1) | (yield self.dut.eem[2].o)
            yield
            yield self.eem[0].io.eq(0)
        yield self.dut.ce_le.eq(1)
        yield
        yield self.cs.eq(0)
        yield self.dut.ce_le.eq(0)
        yield
        yield
        yield
        return miso

    def test(self):
        for i in range(150):
            yield



def main():
    p = Platform()
    dut = Stabilizer(p)
    tb = TB(p, dut)
    run_simulation(tb, [tb.test()], vcd_name="stabilizer.vcd",
            clocks={"sys": 8, "sck1": 8, "sck0": 8,
                "le": 8},
            special_overrides={Tristate: SimTristate, Instance: SimInstance})


if __name__ == "__main__":
    main()