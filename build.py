def main():
    from cpld import Platform
    from stabilizer import Stabilizer

    p = Platform()
    s = Stabilizer(p)
    p.build(s, build_name="stabilizer", mode="cpld")

if __name__ == "__main__":
    main()