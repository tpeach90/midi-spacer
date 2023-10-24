import threading
from time import time

class Player (threading.Thread):

    def __init__(self, mid, port):
        threading.Thread.__init__(self, target=self.play)

        self.port = port
        self.mid = mid

        # time in seconds from the beginning of the song to the beginning of the most recent note.
        self.song_time = 0
        # duration of previous note
        self.prev_note_duration = 0
        # real time at which the previous note started playing
        self.prev_note_start = None


    def play(self):
        self.playing = True

        for msg in self.mid.play():

            if not self.playing:
                break

            self.song_time += self.prev_note_duration

            self.prev_note_start = time()
            self.prev_note_duration = msg.time

            self.port.send(msg)

            print(msg)
        
        self.playing = False
        self.port.reset()

    def get_time(self):
        # returns the current time in the midi file
        return self.song_time + (time() - self.prev_note_start)
