import random
from collections import defaultdict
from functools import wraps
from itertools import islice
from zipfile import ZipFile

from music21 import duration, midi, note, pitch, stream


def midis_from_zip(zip_path):
    '''Read midi files from a zip file.

    TODO: Have this function read midis from all of directories, '.tar.gz',
        '.zip', etc.

    Args:
        zip_path: Path to zip file.

    Returns:
        List of `music21.midi.MidiFile`s.
    '''
    mfs = []
    with ZipFile(zip_path) as zip:
        for filename in (f.filename for f in zip.filelist):
            with zip.open(filename) as f:
                mf = midi.MidiFile()
                mf.file = f  # with context will close f
                mf.read()
            mfs.append(mf)
    return mfs


def ngrams(it, n=2):
    '''Yield ngram tuples from iterable.

    Args:
        it: Iterable to yield ngrams from. Note that this can safely be a
            generator.
    
    Yields:
        Tuples from iterable. For example:

        >>> list(ngrams('trigrams', 3))
        [('t', 'r', 'i'), ('r', 'i', 'g'), ('i', 'g', 'r'), ('g', 'r', 'a'),
         ('r', 'a', 'm'), ('a', 'm', 's')] 
    '''
    it = list(it)
    yield from zip(*(islice(it, i, None) for i in range(n)))


def pitch_to_note(func):
    '''TODO: don't use this.
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        pitch = func(*args, **kwargs)
        n = note.Note(pitch)
        return n
    return wrapper


class State(object):
    '''Representation of states in Markov transition.
    '''
    def __init__(self, pitch):
        self.pitch = pitch

        # state -> count
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
    '''Learn transitions from notes.
    '''
    note_info = (note.pitch for note in notes)
    transitions = ngrams(note_info, n=n)

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


def notes_from_part(part):
    return [n for n in part
            if isinstance(n, note.Note)]


def save_midi():
    pass


if __name__ == '__main__':
    midis = midis_from_zip('bwv1007.zip')
    n = 7
    scores = [midi.translate.midiFileToStream(m) for m in midis]
    notes = sum((notes_from_part(score[0]) for score in scores), [])
    states = transitions(notes, n=n)
    new_notes = sample_markov(notes, states, num_notes=200, dur=0.5, n=n)
    # play_notes(new_notes)     
