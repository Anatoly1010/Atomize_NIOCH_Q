#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from math import exp, sqrt
import datetime
from threading import Thread
from PyQt6 import QtWidgets, uic #, QtCore, QtGui
from PyQt6.QtWidgets import QWidget 
from PyQt6.QtGui import QIcon
import atomize.general_modules.general_functions as general
import atomize.device_modules.Micran_Q_band_MW_bridge as mwBridge

class MainWindow(QtWidgets.QMainWindow):
    """
    A main window class
    """
    def __init__(self, *args, **kwargs):
        """
        A function for connecting actions and creating a main window
        """
        super(MainWindow, self).__init__(*args, **kwargs)
        
        self.destroyed.connect(lambda: self._on_destroyed())         # connect some actions to exit
        # Load the UI Page
        path_to_main = os.path.dirname(os.path.abspath(__file__))
        gui_path = os.path.join(path_to_main,'gui/mw_main_window.ui')
        icon_path = os.path.join(path_to_main, 'gui/icon_mw.png')
        self.setWindowIcon( QIcon(icon_path) )

        uic.loadUi(gui_path, self)                        # Design file

        # configuration data
        self.mw = mwBridge.Micran_Q_band_MW_bridge()

        # Connection of different action to different Menus and Buttons
        self.button_initialize.clicked.connect(self.reset_flags)
        self.button_initialize.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(63, 63, 97);\
         border-style: outset; color: rgb(193, 202, 227); font-weight: bold; }\
          QPushButton:pressed {background-color: rgb(211, 194, 78); ; border-style: inset}")
        self.button_off.clicked.connect(self.turn_off)
        self.button_off.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(63, 63, 97);\
         border-style: outset; color: rgb(193, 202, 227); font-weight: bold; }\
          QPushButton:pressed {background-color: rgb(211, 194, 78); ; border-style: inset}")
        self.button_telemetry.clicked.connect(self.telemetry)
        self.button_telemetry.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(63, 63, 97);\
         border-style: outset; color: rgb(193, 202, 227); font-weight: bold; }\
          QPushButton:pressed {background-color: rgb(211, 194, 78); ; border-style: inset}")

        # text labels
        self.label.setStyleSheet("QLabel { color : rgb(193, 202, 227); font-weight: bold; }")
        self.label_2.setStyleSheet("QLabel { color : rgb(193, 202, 227); font-weight: bold; }")
        self.label_5.setStyleSheet("QLabel { color : rgb(193, 202, 227); font-weight: bold; }")
        self.label_6.setStyleSheet("QLabel { color : rgb(193, 202, 227); font-weight: bold; }")
        self.label_7.setStyleSheet("QLabel { color : rgb(193, 202, 227); font-weight: bold; }")
        self.label_8.setStyleSheet("QLabel { color : rgb(193, 202, 227); font-weight: bold; }")
        self.label_9.setStyleSheet("QLabel { color : rgb(193, 202, 227); font-weight: bold; }")

        self.telemetry_text.setStyleSheet("QPlainTextEdit { color : rgb(211, 194, 78); }") # rgb(193, 202, 227)
        
        # Spinboxes
        self.Att1_prd.valueChanged.connect(self.att1_prd)
        self.Att1_prd.lineEdit().setReadOnly( True )   # block input from keyboard
        self.Att1_prd.setStyleSheet("QDoubleSpinBox { color : rgb(193, 202, 227); }")
        self.Att2_pin.valueChanged.connect(self.att2_pin)
        #self.Att2_pin.lineEdit().setReadOnly( True )
        self.Att2_pin.setStyleSheet("QDoubleSpinBox { color : rgb(193, 202, 227); }")
        self.Att1_prm.valueChanged.connect(self.att1_prm)
        self.Att1_prm.lineEdit().setReadOnly( True )
        self.Att1_prm.setStyleSheet("QSpinBox { color : rgb(193, 202, 227); }")
        self.Att2_prm.valueChanged.connect(self.att2_prm)
        self.Att2_prm.lineEdit().setReadOnly( True )
        self.Att2_prm.setStyleSheet("QDoubleSpinBox { color : rgb(193, 202, 227); }")
        self.Synt.valueChanged.connect(self.synt)
        self.Synt.setStyleSheet("QSpinBox { color : rgb(193, 202, 227); }")

        self.Rot_vane.valueChanged.connect(self.rot_vane)
        #self.Rot_vane.lineEdit().setReadOnly( True )
        self.Rot_vane.setStyleSheet("QDoubleSpinBox { color : rgb(193, 202, 227); }")

        self.Cuttoff_box.setStyleSheet("QComboBox { color : rgb(193, 202, 227); selection-color: rgb(211, 194, 78); }")
        self.Cuttoff_box.currentIndexChanged.connect(self.cutoff_changed)

        self.curr_dB = 60
        self.prev_dB = 60
        self.p1 = 'None'

        text_open = self.mw.mw_bridge_open()
        self.telemetry_text.appendPlainText( text_open )
        self.mw.mw_bridge_reset()
        self.mw.mw_bridge_initialize(state = 'On')

        self.initialize()
        
        text_init = self.mw.mw_bridge_telemetry()
        self.telemetry_text.appendPlainText( text_init )

    def _on_destroyed(self):
        """
        A function to do some actions when the main window is closing.
        """    
        self.initialize_at_exit()
        general.wait('300 ms')
        self.mw.mw_bridge_close()
        
        try:
            self.p1.join()
        except ( AttributeError, NameError, TypeError ):
            pass

    def quit(self):
        """
        A function to quit the programm
        """
        self.initialize_at_exit()

        try:
            self.p1.join()
        except ( AttributeError, NameError, TypeError ):
            pass

        general.wait('300 ms')
        self.mw.mw_bridge_close()
        sys.exit()

    def att1_prd(self):
        """
        A function to send a value to the attenuator 1 in the PRD channel
        """
        param = self.Att1_prd.value()
        self.mw.mw_bridge_att1_prd( param )
        answer = self.mw.mw_bridge_att1_prd()
        self.telemetry_text.appendPlainText( answer )

    def att2_pin(self):
        """
        A function to send a value to the attenuator 2 in the PRD channel
        """
        param = self.Att2_pin.value()
        self.mw.mw_bridge_att_pin( param )
        answer = self.mw.mw_bridge_att_pin()
        self.telemetry_text.appendPlainText( answer )

    def att1_prm(self):
        """
        A function to send a value to the attenuator 1 in the PRM channel
        """
        param = self.Att1_prm.value()
        self.mw.mw_bridge_att_prm( param )
        answer = self.mw.mw_bridge_att_prm()
        self.telemetry_text.appendPlainText( answer )

    def att2_prm(self):
        """
        A function to send a value to the attenuator 2 in the PRM channel
        """
        param = self.Att2_prm.value()
        self.mw.mw_bridge_att2_prm( param )
        answer = self.mw.mw_bridge_att2_prm()
        self.telemetry_text.appendPlainText( answer )

    def cutoff_changed(self):
        """
        A function to change the bandwidth of the video amplifier
        """
        txt_raw = str( self.Cuttoff_box.currentText() )
        txt = txt_raw.split(" ")[0]

        self.mw.mw_bridge_cut_off( txt )
        answer = self.mw.mw_bridge_cut_off()
        self.telemetry_text.appendPlainText( answer )

    def synt(self):
        """
        A function to change the frequency
        """

        param = int( self.Synt.value() / 5 )
        self.Synt.setValue( int(param * 5) ) 
        temp = str(param)

        self.mw.mw_bridge_synthesizer( param )
        answer_raw = int( self.mw.mw_bridge_synthesizer().split(" ")[1] ) * 5
        answer = 'Frequency: ' + str( answer_raw ) + ' MHz'
        self.telemetry_text.appendPlainText( str(answer) )

    def pause_and_label(self, time):
        self.label_9.setStyleSheet("QLabel { color : rgb(255, 0, 0); font-weight: bold; }")
        general.wait( time )
        self.label_9.setStyleSheet("QLabel { color : rgb(193, 202, 227); font-weight: bold; }")
    
    def pause_and_label_exit(self, time):
        general.wait( time )

    def rot_vane(self):
        """
        A function to send a value to the rotary vane attenuator
        """
        param = self.Rot_vane.value()
        self.curr_dB = round( float( param ), 1 )
    
        step = int( self.calibration( self.curr_dB ) ) - int( self.calibration( self.prev_dB ) )

        try:
            self.p1.join()
        except ( AttributeError, NameError, TypeError ):
            pass

        self.mw.mw_bridge_rotary_vane(self.curr_dB, mode = 'Arbitrary')

        # 60 is a manual calibration
        time_to_wait = abs( 60 * step )

        self.p1 = Thread(target = self.pause_and_label, args = (str(time_to_wait) + ' ms', ) )
        self.p1.start()
        
        answer = self.mw.mw_bridge_rotary_vane( )
        self.telemetry_text.appendPlainText( answer )

        self.prev_dB = self.curr_dB

    def reset_flags(self):
        """
        A function to initialize a bridge.
        """
        self.mw.mw_bridge_reset()

    def initialize(self):
        """
        A function to initialize a bridge.
        """
        self.synt()

        self.cutoff_changed()
        self.att1_prd()
        self.att2_pin()
        self.att1_prm()
        self.att2_prm()

        # Rotary vane to 60 dB
        self.mw.mw_bridge_rotary_vane(60, mode = 'Limit')

        self.p1 = Thread(target = self.pause_and_label, args = ( '5 s', ) )
        self.p1.start()
            
        self.curr_dB = 60
        self.prev_dB = 60

    def initialize_at_exit(self):
        """
        A function to initialize a bridge.
        """

        # Rotary vane to 60 dB
        step = int( self.calibration( 60 ) ) - int( self.calibration( self.prev_dB ) )
        
        self.mw.mw_bridge_rotary_vane( 60, mode = 'Arbitrary')

        self.mw.mw_bridge_initialize(state = 'Off')

        time_to_wait = abs( 60 * step )

        self.p1 = Thread(target = self.pause_and_label_exit, args = ( str(time_to_wait) + ' ms', ) )
        self.p1.start()
        
        self.curr_dB = 60
        self.prev_dB = 60

    def turn_off(self):
        """
         A function to turn off a bridge.
        """
        self.quit()

    def telemetry(self):
        """
        A function to get the telemetry.
        """
        text = self.mw.mw_bridge_telemetry() 
        self.telemetry_text.appendPlainText( text )

    def help(self):
        """
        A function to open a documentation
        """
        pass

    def calibration(self, x):
        # approximation curve
        # step to dB
        return -4409.48 + 676.179 * exp( -0.0508708 * x ) + 2847.41 * exp( 0.00768761 * x ) - 0.345934 * x ** 2 + 2847.41 * exp( 0.00768761 * x ) - 440.034 * sqrt( x )

def main():
    """
    A function to run the main window of the programm.
    """
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
