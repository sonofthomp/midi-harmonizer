from utils import *
from sys import argv

if __name__ == '__main__':
	midi_in = argv[1]
	mp3_out = argv[2]

	gen_tone_file(midi_in, mp3_out)