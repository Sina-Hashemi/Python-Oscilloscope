# Sina Hashemi , Mahan Zamani , Muhammadhossein Sabzalian

import sys
import math
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget,QSplitter, QFrame, QSlider, QMessageBox)

MAX_POSSIBLE_VOLTAGE = 300

class OscilloscopeGUI(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Oscilloscope")
		self.setGeometry(100, 100, 800, 400)  # Set window position and size
		self.initialize_parameters()
		self.initialize_ui()
		self.initialize_audio()
	
	def initialize_parameters(self):
		"""Initialize key parameters for the oscilloscope."""
		self.common_volt_divs = [10, 20, 50, 100, 200, 500, 1000]
		self.voltage_div = self.common_volt_divs[4]
		self.time_div = 100
	
	def initialize_ui(self):
		"""Initialize the user interface components."""
		self.initialize_buttons()
		self.initialize_sliders()
		self.initialize_labels()
		self.setup_layout()
	
	def initialize_buttons(self):
		"""Create and configure the main control buttons."""
		self.start_stop_button = QPushButton("Start")
		self.quit_button = QPushButton("Quit")
		self.start_stop_button.clicked.connect(self.toggle_stream)
		self.quit_button.clicked.connect(self.close)
		
	def initialize_sliders(self):
		"""Create and configure the sliders for adjusting voltage/div and time/div."""
		self.voltage_slider = QSlider(Qt.Horizontal)
		self.voltage_slider.setRange(0, 6)
		self.voltage_slider.setValue(4)
		self.voltage_slider.setTickPosition(QSlider.TicksBelow)
		self.voltage_slider.setTickInterval(1)
		self.voltage_slider.valueChanged.connect(self.update_voltage_div)
		self.time_slider = QSlider(Qt.Horizontal)
		self.time_slider.setRange(-3, 6)
		self.time_slider.setValue(int(math.log(self.time_div, 10)))
		self.time_slider.setTickPosition(QSlider.TicksBelow)
		self.time_slider.setTickInterval(1)
		self.time_slider.valueChanged.connect(self.update_time_div)
		
	def initialize_labels(self):
		"""Create and configure labels for displaying information."""
		self.freq_label = QLabel("Frequency: N/A")
		self.amp_label = QLabel("Amplitude: N/A")
		self.voltage_label = QLabel(f"Voltage/Div: {self.voltage_div}")
		self.time_label = QLabel(f"Time/Div: {self.time_div}")
		
	def setup_layout(self):
		"""Arrange all UI elements into the main layout."""
		button_layout = QVBoxLayout()
		button_layout.addWidget(self.start_stop_button)
		button_layout.addWidget(self.freq_label)
		button_layout.addWidget(self.amp_label)
		button_layout.addWidget(self.time_label)
		button_layout.addWidget(self.time_slider)
		button_layout.addWidget(self.voltage_label)
		button_layout.addWidget(self.voltage_slider)
		button_layout.addWidget(self.quit_button)
		button_widget = QWidget()
		button_widget.setLayout(button_layout)
		splitter = QSplitter(Qt.Horizontal)
		splitter.addWidget(button_widget)
		self.figure, self.ax = plt.subplots()
		self.canvas = self.figure.canvas
		splitter.addWidget(self.canvas)
		splitter.setSizes([200, 600])
		central_widget = QFrame(self)
		central_layout = QVBoxLayout(central_widget)
		central_layout.addWidget(splitter)
		self.setCentralWidget(central_widget)
	
	def initialize_audio(self):
		"""Initialize the audio stream and timer."""
		self.p = pyaudio.PyAudio()
		self.stream = None
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_plot)
		self.stream_active = False
	
	def toggle_stream(self):
		"""Toggle the audio stream on or off."""
		if self.stream_active:
			self.stop_stream()
		else:
			self.start_stream()
		
	def start_stream(self):
		"""Start the audio stream and timer."""
		self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
		self.timer.start(100)
		self.start_stop_button.setText("Stop")
		self.stream_active = True
		
	def stop_stream(self):
		"""Stop the audio stream and timer."""
		if self.stream:
			self.stream.stop_stream()
			self.stream.close()
			self.timer.stop()
			self.start_stop_button.setText("Start")
			self.stream_active = False
	
	def update_plot(self):
		"""Update the oscilloscope plot with the latest audio data."""
		data = np.fromstring(self.stream.read(1024), dtype=np.int16)
		voltage_data = self.voltage_div * (data / (2 ** 15))
		self.ax.clear()
		self.ax.plot(voltage_data)
		self.ax.set_xlim(0, len(data))
		self.ax.set_ylim(-self.voltage_div, self.voltage_div)
		self.canvas.draw()
		self.update_frequency_and_amplitude(voltage_data)
	
	def update_frequency_and_amplitude(self, voltage_data):
		"""Update the frequency and amplitude labels with the latest data."""
		fft_signal = np.fft.fft(voltage_data)
		fft_signal = np.abs(fft_signal)
		frequency = np.fft.fftfreq(len(fft_signal), 1 / 44100)
		half_range = len(frequency) // 2
		frequency = frequency[:half_range]
		fft_signal = fft_signal[:half_range]
		peak_freq = frequency[np.argmax(fft_signal)]
		amplitude = np.max(np.abs(voltage_data))
		self.freq_label.setText(f"Frequency: {peak_freq:.2f} Hz")
		self.amp_label.setText(f"Amplitude: {amplitude:.2f} mV")
		if amplitude > MAX_POSSIBLE_VOLTAGE:
			self.alert_amplitude_exceeded(amplitude)

		# if you experience error "OSError: [Errno -9981] Input overflowed" uncomment the next two lines
		# self.stop_stream()
		# self.start_stream()

	def update_voltage_div(self, value):
		"""Update the voltage division based on slider value."""
		self.voltage_div = self.common_volt_divs[value]
		self.voltage_label.setText(f"Voltage/Div: {self.voltage_div}")
		self.ax.set_ylim(-self.voltage_div, self.voltage_div)
		self.canvas.draw()
	
	def update_time_div(self, value):
		"""Update the time division based on slider value."""
		self.time_div = 10 ** value
		self.time_label.setText(f"Time/Div: {self.time_div}")
		self.ax.set_xlim(0, self.time_div)
		self.canvas.draw()
		
	def alert_amplitude_exceeded(self, amplitude):
		"""Show an alert when the amplitude exceeds the maximum possible voltage."""
		alert_label = QLabel(f"Warning: Amplitude exceeded!\nAmplitude: {amplitude:.2f} mV", self)
		alert_label.setStyleSheet("QLabel { background-color : red; color : white; padding: 10px; }")
		alert_label.setGeometry(200, 0, 400, 50)
		alert_label.show()
		QTimer.singleShot(1000, alert_label.hide)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = OscilloscopeGUI()
	window.show()
	sys.exit(app.exec_())
