from utils import *
from sys import argv

if __name__ == '__main__':
	midi_in = argv[1]
	mp3_in = argv[2]
	mp3_out = argv[3]

	vocode_to_midi(midi_in, mp3_in, mp3_out)