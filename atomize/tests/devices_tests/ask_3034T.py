import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Keysight_3000_Xseries as key

xs = []
ys = []
data = []

t3034 = key.Keysight_3000_Xseries()


t3034.oscilloscope_trigger_channel('Line')
a = t3034.oscilloscope_record_length()
t3034.oscilloscope_record_length(5000)
t3034.oscilloscope_stop()
b = t3034.oscilloscope_timebase( )
#t3034.oscilloscope_acquisition_type('Average')
#t3034.oscilloscope_stop()

general.message( a, b )

#x = np.arange(4000)

for i in range(4):
    start_time = time.time()
    t3034.oscilloscope_start_acquisition()
    y = t3034.oscilloscope_get_curve('CH1')
    general.message(str(time.time() - start_time))
    data.append(y)
    general.plot_2d('Plot Z Test2', data, start_step=((0,1),(0.3,1)), xname='Time',\
        xscale='s', yname='Magnetic Field', yscale='T', zname='Intensity', zscale='V')

    


#general.message(str(time.time() - start_time))