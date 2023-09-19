"""PSOLA-based MIDI harmonizer, written by Gabriel Thompson"""

from mido import MidiFile
import soundfile as sf
import numpy as np
import psola

midi_to_hz = lambda midi: 220*(2**((midi-57)/12))

def gen_note_times(tracks: list) -> tuple[int, list[list[int]]]:
	"""Given MIDI tracks, returns the tempo of the tracks and the times when the notes
	occur in each of the tracks

	Args
		tracks (list): A list of MIDI tracks

	Returns
		tuple[int, list[list[int]]]: List of when each of the notes occurs in each track
	"""
	note_times = [[] for pitch in range(128)]
	tempo = 0

	for track in tracks:
		cur_time = 0
		for msg in track:
			if msg.type == 'set_tempo':
				tempo = msg.tempo
			    
			if msg.type != 'note_on':
				continue
			    
			note = msg.note
			time = msg.time
			vel = msg.velocity
			cur_time += time

			if (vel == 0) and note_times[note]:
				note_times[note][-1].append(cur_time)

			if vel != 0:
				note_times[note].append([cur_time])

	for note in range(128):
		if note_times[note] and len(note_times[note][-1]) == 1:
			note_times[note][-1].append(cur_time)
	        
	return tempo, note_times


def gen_cutoffs(note_times: list[list[int]]) -> tuple[list, dict, dict]:
	"""Generates list of note cutoff times, dictionary mapping note cutoff times to
	rounded note cutoff times, and dictionary mapping note cutoff times to note cutoff
	indices

	Args:
		note_times (list[list[int]]): List of windows of time when notes are played (per
									  track)

	Returns:
		tuple[list, dict, dict]: A list of note cutoff times, a dictionary mapping note
								 cutoff times to rounded note cutoff times, and
								 dictionary mapping note cutoff times to note cutoff
								 indices
	"""
	_cutoffs_set = set([
		time
		for note in note_times
		for section in note
		for time in section[:2]
	])
	cutoffs_list = list(_cutoffs_set)
	cutoffs_list.sort()
	
	cutoffs_map = {
		cutoff: cutoff
		for cutoff in cutoffs_list
	}
	
	index = 0
	while index < (len(cutoffs_list) - 1):
		a,b = cutoffs_list[index], cutoffs_list[index + 1]
		if (b - a) < 200:
			cutoffs_map[cutoffs_list[index + 1]] = cutoffs_list[index]
			del cutoffs_list[index + 1]
		else:
			index += 1

	cutoffs_dict = {
		time: index
		for index, time in enumerate(cutoffs_list)
	}
	return (cutoffs_list, cutoffs_dict, cutoffs_map)


def actually_insert_note(time_range: list, cutoffs_dict: dict, note: int, lo: int, hi: int) -> None:
	"""Adds note into the appropriate spot of time range according to specifications"""
	lo_index = cutoffs_dict[lo]
	hi_index = cutoffs_dict[hi]
	time_range[lo_index:hi_index] = [
		note
		for i in range(lo_index, hi_index)
	]


def check_if_note_fits(time_blocks: list, cutoffs_dict: dict, note: int, lo: int, hi: int) -> bool:
	"""Returns True or False depending on whether the note fits into the time blocks"""
	lo_index = cutoffs_dict[lo]
	hi_index = cutoffs_dict[hi]
	if all([
		cur_note == 0
		for cur_note in time_blocks[lo_index:hi_index]
	]):
		return True
	return False
    

def insert_voice(time_blocks: list, cutoffs_dict: dict, cutoffs_map: dict, note: int, lo: int, hi: int) -> None:
	"""Inserts note into given time blocks array as specified"""
	for voice in time_blocks:
		if check_if_note_fits(voice, cutoffs_dict, note, cutoffs_map[lo], cutoffs_map[hi]):
			actually_insert_note(voice, cutoffs_dict, note, cutoffs_map[lo], cutoffs_map[hi])
			return

	time_blocks.append([
		0
		for i in range(len(cutoffs_dict) - 1)
	])

	actually_insert_note(time_blocks[-1], cutoffs_dict, note, cutoffs_map[lo], cutoffs_map[hi])


def gen_time_blocks(tracks: list) -> tuple[list, dict, list]:
	"""Generates three things:
	 - A list of time cutoffs of MIDI notes
	 - A dictionary mapping cutoff times to the indices of the cutoff
	 - A list of time blocks

	Args:
		tracks (list): List of MIDI tracks generated from the mido module

	Returns:
		list, dict, list: a list of time cutoffs of MIDI notes, a dictionary mapping
						  cutoff times to the indices of the cutoff, a list of time
						  blocks
	"""
	time_blocks = []
	tempo, note_times = gen_note_times(tracks)
	cutoffs_list, cutoffs_dict, cutoffs_map = gen_cutoffs(note_times)
	
	for midi, times in enumerate(note_times):
		for time_range in times:
			lo, hi = time_range[:2]
			insert_voice(time_blocks, cutoffs_dict, cutoffs_map, midi, lo, hi)

	return cutoffs_list, cutoffs_dict, time_blocks


def get_length_of_midi(mid: MidiFile, tempo: int, note_times: list[list[int]]) -> float:
	"""Return length of MIDI file when played (in seconds)

	Args:
		mid (MidiFile): MIDI file object (parsed from mido)
		tempo (int): Tempo of the MIDI file (time in microseconds between beats)
		note_times (list[list[int]]): List of windows of when a note is played

	Returns:
		float: How many seconds the MIDI file is played for
	"""
	total_ticks = max([
		end_time
		for pitch_blocks in note_times
		for start_time, end_time in pitch_blocks
	])
	return (tempo / 1_000_000) * (total_ticks / mid.ticks_per_beat)


def gen_tone_of_length(seconds: float, freq=200.0) -> np.array:
	"""Returns an array of the waveform of a given frequency for a given amount of
	seconds

	Args:
		seconds (float): Number of seconds for the frequency to play for
		freq (float): Frequency (in Hz)

	Returns:
		np.array: Waveform of the frequency with the specific parameters
	"""
	return list(np.sin(np.arange(
		0, 2*np.pi*freq*seconds, 2*np.pi*freq/44100
	)))


def gen_freq_tracks_from_blocks(time_blocks: list[list[int]], cutoffs_list: list[int], cutoffs_dict: dict[int, int]) -> np.array:
	"""Given information about MIDI file, returns a 2D array of frequencies per track
	per time

	Args:
		time_blocks (list[list[int]]): 2-dimensional array of frequencies occuring per
									   track per time block
		cutoffs_list (list[int]): List of cutoffs between time blocks
		cutoffs_dict (dict[int, int]): Mapping of cutoff times to cutoff indices

	Returns:
		np.array: The pitches of each frequency track per time
	"""
	freq_tracks = np.zeros([len(time_blocks), max(cutoffs_dict.keys())])

	for block_index, block in enumerate(time_blocks):
		for note_index, note in enumerate(block):
			lo = cutoffs_list[note_index]
			hi = cutoffs_list[note_index + 1]
			freq_tracks[block_index][np.arange(lo, hi)] = midi_to_hz(note)
	        
	return freq_tracks


def gen_freq_tracks(filepath: str) -> np.array:
	"""Given a path to a MIDI file, generates a 2-D array of the frequency information
	of each track in the MIDI file over time.

	Args:
		filepath (str): Path to MIDI file to be parsed

	Returns:
		np.array: 2-D array where each item of each subarray represents the pitch in
		each track at each time
	"""
	mid = MidiFile(filepath, clip=True)

	cutoffs_list, cutoffs_dict, time_blocks = gen_time_blocks(mid.tracks)
	freq_tracks = gen_freq_tracks_from_blocks(time_blocks, cutoffs_list, cutoffs_dict)
	
	return freq_tracks


def gen_vocoded_waveform(sound: np.array, freq_tracks: np.array) -> np.array:
	"""Given a waveform and an array of "frequency tracks" (which contain the frequency
	per time in each vocal track) harmonizes the waveform to each frequency array and
	sums each harmony. Harmonization is done using psola.vocode.

	Args:
		sound (np.array): Audio waveform to be harmonized
		freq_tracks (np.array): Array of frequency arrays

	Returns:
		np.array: Sum of original audio waveform harmonized to each frequency array
	"""
	full = np.zeros(len(sound))

	for freq_track in freq_tracks:
		# Partially taken from https://thewolfsound.com/how-to-auto-tune-your-voice-with-python/
		vocoded = psola.vocode(sound,
					sample_rate=int(44100),
					target_pitch=freq_track,
					fmin=65.41,   # C2 = 65.41 Hz
					fmax=2093.00) # C7 = 2093.00 Hz

		size_ratio = len(sound) / len(freq_track)
		zeros_indices = [
			int(index * size_ratio + offset)
			for index, i in enumerate(freq_track) if i < 10
			for offset in range(int(size_ratio // 1 + 1))
		]
		included = [0 for i in range(int(len(zeros_indices)))]
		for i in zeros_indices:
			included.append(int(i / size_ratio))

		vocoded[zeros_indices] = 0
		full += vocoded

	full /= len(freq_tracks)
	return full


def add_metronome(vocoded: np.array, tempo: int) -> np.array:
	"""Given a waveform and a tempo, adds a metronome to it according to the tempo. Used
	for testing, not in final product.

	Args:
		vocoded (np.array): Audio waveform
		tempo (int): Tempo of the audio

	Returns:
		np.array: The waveform with the metronome added
	"""
	skip = int((tempo / 1_000_000) * 44100)
	
	for start_index in range(0, len(vocoded), skip):
		for index in range(start_index, start_index + 20):
			vocoded[index] = 1
	    
	return vocoded


def vocode_to_midi(midi_in: str, mp3_in: str, mp3_out: str) -> None:
	"""Runs the phase vocoding algorithm on a MP3 input file according to a MIDI file,
	outputs the result to an MP3 output file

	Args:
		midi_in (str): Path to MIDI input file
		mp3_in (str): Path to MP3 input file
		mp3_out (str): Path to MP3 output file

	Returns:
		None
	"""
	if not(midi_in.endswith('.mid')):
		raise Exception('Not a MIDI file')
    
	if not(mp3_in.endswith('.mp3')):
		raise Exception('Not an MP3 file')
        
	freq_tracks = gen_freq_tracks(midi_in)
	waveform, sample_rate = sf.read(mp3_in)
	vocoded = gen_vocoded_waveform(waveform, freq_tracks)
	
	file_prefix = mp3_in[:-4]
	sf.write(mp3_out, vocoded, 44100)


def gen_tone_file(midi_in: str, mp3_out: str) -> None:
	"""Runs the phase vocoding algorithm on a pure sine wave according to a MIDI file,
	and outputs the result to an MP3 output file

	Args:
		midi_in (str): Path to MIDI input file
		mp3_out: Path to MP3 output file

	Returns:
		None
	"""
	if not(midi_in.endswith('.mid')):
		raise Exception('Not a MIDI file')
	       
	file_prefix = midi_in[:-4]
	mid = MidiFile(midi_in, clip=True)
	tracks = mid.tracks
	
	tempo, note_times = gen_note_times(tracks)
	length_of_midi = get_length_of_midi(mid, tempo, note_times)
	tone = gen_tone_of_length(length_of_midi)
	freq_tracks = gen_freq_tracks(midi_in)
	
	vocoded = gen_vocoded_waveform(tone, freq_tracks)
	sf.write(mp3_out, vocoded, 44100)
