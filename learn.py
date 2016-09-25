from zipfile import ZipFile
from music21 import midi, stream, note, pitch, duration
from collections import defaultdict
from itertools import islice
import random
from functools import wraps


def midis_from_zip(zip_path):
    mfs = []
    with ZipFile(zip_path) as zip:
        for filename in (f.filename for f in zip.filelist):
            with zip.open(filename) as f:
                mf = midi.MidiFile()
                mf.file = f
                mf.read()
            mfs.append(mf)
    return mfs


def ngrams(it, n=2):
    it = list(it)
    yield from zip(*(islice(it, i, None) for i in range(n)))

def pitch_to_note(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        pitch = func(*args, **kwargs)
        n = note.Note(pitch)
        return n
    return wrapper

class State(object):
    def __init__(self, pitch):
        self.pitch = pitch
        
        # state->count
        self.target_counts = defaultdict(int)
        self.target_probs = {}

    def update(self, pitch, count):
        self.target_counts[pitch] += count

    def compute_probabilities(self):
        z = sum(self.target_counts.values())
        for key, value in self.target_counts.items():
            self.target_probs[key] = value / z
        return self.target_probs
        
    @pitch_to_note
    def sample_transition(self):
        x = random.random()
        for key, prob in self.target_probs.items():
            if prob > x:
                return key
            x -= prob
        return key
        
def transitions(notes, n=2):
    note_info = (note.pitch for note in notes)
    transitions = ngrams(note_info, n=n)

    #counts = Counter(ngrams(note_info, n=2))
    
    states = {}
    for t in transitions:
        *source, target = t
        source = tuple(source)
        if source not in states:
            states[source] = State(pitch)
        states[source].update(target, 1)

    for state in states.values():
        state.compute_probabilities()
        
    return states


def sample_markov(source_notes, states, num_notes=100, dur=1, n=2):
    curr_source = tuple([note.pitch for note in source_notes[:n - 1]])
    notes = []
    for _ in range(num_notes):
        curr_state = states[curr_source]
        next_note = curr_state.sample_transition()
        next_note.duration.quarterLength = dur
        notes.append(next_note)
        curr_source = tuple(list(curr_source[1:]) + [next_note.pitch])
    return notes


n = 7
scores = [midi.translate.midiFileToStream(m) for m in midis]
notes = sum((notes_from_part(score[0]) for score in scores), [])
states = transitions(notes, n=n)
new_notes = sample_markov(notes, states, num_notes=200, dur=0.5, n=n)
# play_notes(new_notes)     
