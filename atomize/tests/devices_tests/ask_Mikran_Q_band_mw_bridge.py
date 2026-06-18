import atomize.general_modules.general_functions as general
import atomize.device_modules.Mikran_Q_band_MW_bridge as mwBridge

mw = mwBridge.Mikran_Q_band_MW_bridge()

#general.message( mw.mw_bridge_name() )

mw.mw_bridge_open()

#general.message( mw.mw_bridge_telemetry() )

#mw.mw_bridge_synthesizer('6800')
#general.message( mw.mw_bridge_synthesizer() )

#mw.mw_bridge_att1_prd('10')
#general.message( mw.mw_bridge_att1_prd() )

#mw.mw_bridge_att_pin('15')
#general.message( mw.mw_bridge_att_pin() )

#mw.mw_bridge_att_prm('10.5')
#general.message( mw.mw_bridge_att_prm() )

#general.message( mw.mw_bridge_att2_prm('0') )
#general.message( mw.mw_bridge_att2_prm() )

#mw.mw_bridge_cut_off('300')
#general.message( mw.mw_bridge_cut_off() )

mw.mw_bridge_rotary_vane(30, mode = 'Arbitrary')

mw.mw_bridge_close()