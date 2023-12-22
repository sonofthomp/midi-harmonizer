# MIDIHarm - a PSOLA-based MIDI vocal harmonizer

Python tool for [pitch-shifting](https://en.wikipedia.org/wiki/Pitch_shifting) MP3 files to MIDI files.

#### Usage
 1. Clone the GitHub repo to your computer with `git clone https://github.com/sonofthomp/midi-harmonizer.git`. Run `cd midi-harmonizer` to enter the directory.
 2. Install the package requirements with `pip install -r requirements.txt`
 3. The harmonization happens in two steps. First, generate a "tone file" -- this will be an MP3 file which you should use a guide to sing the melody of the song to. You can generate this with: `python3 gen_tone.py <path to MIDI file, should end with .mid> <path you want the tone outputted to, should end with .mp3>`
 4. Record yourself singing along to the "tone file" generated from the MIDI file. Store this in a file somewhere on your computer and take note of its location.
 5. From the same directory as the cloned repo, run `python3 gen_harmonies.py <path to MIDI file, should end with .mid> <path to you singing, should end with .mp3> <path you want the pitch-corrected version outputed to, should end with .mp3>`

#### Samples:
 - ["The Longest Time"](https://drive.google.com/file/d/1iUiS8SRIryN8G8qwq9o78cquQxJUPypE/view?usp=drive_link) (Billy Joel)
 - ["Nobody Loves You Like Me"](https://drive.google.com/file/d/1KdWddgADgaVQdM9znTTMILs2XiYXQube/view?usp=sharing) (Jonathan Coulton)
 - ["Auld Lang Syne"](https://drive.google.com/file/d/1xyOqZ27ZsNG_-O0BwCoFYj3t36gOs7qO/view?usp=drive_link) (traditional)
 - ["Doin' it Right"](https://drive.google.com/file/d/1CYurlsZ7FwWxdIHys09cVGsmYJxQpjOW/view?usp=drive_link) (Daft Punk)
 - ["Hide and Seek"](https://drive.google.com/file/d/149RHfQG-ayPsHujy_P2BnopD-gryqDz8/view?usp=drive_link) (Imogen Heap)
 - ["Lift Every Voice And Sing"](https://drive.google.com/file/d/1awitkiQC4OODjSJnnFJ6-BAarys9Rs8J/view?usp=drive_link) (James Weldon Johnson and J. Rosamond Johnson)
 - ["The Wellerman"](https://drive.google.com/file/d/1uJfRjTb7sCOomo_X-7uDSwquY8roJ-BV/view?usp=drive_link) (traditional, arr. The Longest Johns)

#### How Does This Work?
The algorithm used for pitch-shifting is called [PSOLA](https://en.wikipedia.org/wiki/PSOLA), specifically [Max Morrison's Python implementation](https://github.com/maxrmorrison/psola) of it. The program first reads a MIDI file and extracts the note times from it, then groups these into separate vocal tracks, and then pitch-corrects the MP3 file to each track using the PSOLA library. These harmonized tracks are then summed and the result is outputted to an MP3 file.
