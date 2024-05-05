from writer import Writer
from utime import ticks_ms
from ssd1306 import SSD1306_I2C
import VL53L0X
import machine
import freesans20, font6

CALIB = 0
OBJECT = 1
WAITING = 3
N_READS = 2

state = CALIB
dists = []
fastest = 99.99
last = 99.99
start = ticks_ms()


def avg(l):
    return sum(l) / len(l)


ssd = SSD1306_I2C(128, 64, machine.SoftI2C(scl=machine.Pin(2), sda=machine.Pin(26)))
tof = VL53L0X.VL53L0X(
    machine.SoftI2C(scl=machine.Pin(4), sda=machine.Pin(5), freq=100000)
)

wri_lg = Writer(ssd, freesans20, verbose=False)
wri_sm = Writer(ssd, font6, verbose=False)
Writer.set_textpos(ssd, 32, 0)
wri_sm.printstring("current")

reads = [0] * N_READS
idx = 0
tof.start()
while 1:
    t = ticks_ms()
    # Keep a running average of reads to prevent ghost triggers
    reads[idx] = tof.read()
    idx += 1
    if idx >= N_READS:
        idx = 0
    d = sum(reads) / N_READS

    if t // 100 % 5 == 0:  # Every 500ms
        dists.append(d)
        if len(dists) > 10:
            del dists[0]
        avg_d = avg(dists)
        # print(avg_d)

    if state == CALIB:
        dists.append(d)
        if len(dists) >= 10:
            state = WAITING
        avg_d = avg(dists)

    elif state == WAITING:
        if d < avg_d * 0.5:
            last = (t - start) / 1000
            start = t
            if last < fastest:
                fastest = last
            ssd.fill(0)  # Clear screen
            Writer.set_textpos(ssd, 0, 0)
            wri_sm.printstring("last lap")
            Writer.set_textpos(ssd, 11, 0)
            wri_lg.printstring(f"{last:.2f}")
            Writer.set_textpos(ssd, 32, 0)
            wri_sm.printstring("current")
            Writer.set_textpos(ssd, 16, 64)
            wri_sm.printstring("fastest")
            Writer.set_textpos(ssd, 27, 64)
            wri_lg.printstring(f"{fastest:.2f}")
            state = OBJECT

    elif state == OBJECT:
        if d > avg_d * 0.9:
            state = WAITING

    Writer.set_textpos(ssd, 43, 0)
    wri_lg.printstring(f"{(t-start)/1000:.2f}")
    ssd.show()
