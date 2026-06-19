import sys
import signal
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Keysight_3000_Xseries as t3034
import atomize.device_modules.Mikran_Q_band_MW_bridge as mwBridge
import atomize.device_modules.PB_Micran as pb_pro
#import atomize.general_modules.csv_opener_saver as openfile

t3034 = t3034.Keysight_3000_Xseries()
pb = pb_pro.PB_Micran()
mw = mwBridge.Mikran_Q_band_MW_bridge()

mw.mw_bridge_open()

freq_before = int(str( mw.mw_bridge_synthesizer() ).split(' ')[1])

def cleanup(*args):
    mw.mw_bridge_synthesizer( freq_before )
    #pb.pulser_stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)

### Experimental parameters
START_FREQ = 33000
END_FREQ = 35500
STEP = 5
SCANS = 1
AVERAGES = 100
process = 'None'

# PULSES
REP_RATE = '500 Hz'
PULSE_1_LENGTH = '100 ns'
PULSE_1_START = '0 ns'

# NAMES
EXP_NAME = 'Tune Scan'

# setting pulses:
pb.pulser_pulse(name ='P0', channel = 'TRIGGER', start = '0 ns', length = '100 ns')
pb.pulser_pulse(name ='P1', channel = 'MW', start = PULSE_1_START, length = PULSE_1_LENGTH)

pb.pulser_repetition_rate( REP_RATE )
pb.pulser_update()

#
start_fr = START_FREQ // 5
end_fr = END_FREQ // 5
step_fr = STEP // 5

#
t3034.oscilloscope_record_length( 5000 )
real_length = t3034.oscilloscope_record_length( )

points = int( (end_fr - start_fr) / step_fr ) + 1
data = np.zeros( (points, real_length) )
###

#open1d = openfile.Saver_Opener()
t3034.oscilloscope_acquisition_type('Average')
t3034.oscilloscope_trigger_channel('Ext')
#t3034.oscilloscope_record_length( osc_rec_length )
#tb = t3034.oscilloscope_time_resolution()
t3034.oscilloscope_stop()

t3034.oscilloscope_number_of_averages(AVERAGES)

# initialize the power
mw.mw_bridge_synthesizer( START_FREQ )
general.wait('200 ms')
#path_to_file = open1d.create_file_dialog(directory = '')

for j in general.scans(SCANS):
    i = 0
    freq = start_fr

    while freq <= end_fr:
        
        mw.mw_bridge_synthesizer( freq )
        general.wait('200 ms')

        t3034.oscilloscope_start_acquisition()
        y = t3034.oscilloscope_get_curve('CH3')

        data[i] = ( data[i] * (j - 1) + y ) / j

        process = general.plot_2d(EXP_NAME, np.transpose( data ), start_step = ( (0, 1), (start_fr*1000000*5, step_fr*1000000*5) ), xname = 'Time',\
            xscale = 's', yname = 'Frequency', yscale = 'Hz', zname = 'Intensity', zscale = 'V', pr = process, text = 'Scan / Frequency: ' + \
            str(j) + ' / '+ str(freq) )

        #f = open(path_to_file,'a')
        #np.savetxt(f, y, fmt='%.10f', delimiter=' ', newline='\n', header='frequency: %d' % i, footer='', comments='#', encoding=None)
        #f.close()

        freq = round( (step_fr + freq), 3 ) 
        i += 1

    mw.mw_bridge_synthesizer( start_fr )

mw.mw_bridge_synthesizer( freq_before )
general.wait('200 ms')
pb.pulser_stop()
