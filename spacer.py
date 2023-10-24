import mido
import copy
from typing import List



class MyMessage:
    """class to keep the msg and blkfrac together
    """
    def __init__(self, msg: mido.messages.messages.Message, blkfrac: float):
        self.msg = msg
        self.blkpos = blkfrac


def space_notes(target_blklen: float, mid : mido.MidiFile, checkpoints : List[float], tempo: int) -> mido.MidiFile:
    """Create a spaced-apart MidiFile such that every checkpoint is `target_blklen` apart.
    Does not affect the input MidiFile.

    Args:
        target_blklen (float): Time in seconds between consecutive checkpoints in the output.
        mid (mido.MidiFile): Input midi file.
        checkpoints (List[float]): List of timestamps, in seconds, of checkpoints in the input midifile.
        tempo (int): Midi tempo for the output file, as can be gotten from mido.bpm2tempo().

    Returns:
        mido.MidiFile: Spaced midi file
    """


    mid = copy.deepcopy(mid)

    my_messages = []

    # calculate block fractions for messages
    # (starting time of each message as a multiple of the target block length)
    song_time = 0
    for msg in mid:
        if type(msg) is mido.messages.messages.Message:

            # number of checkpoints before this message
            blknum = len([chkpt for chkpt in checkpoints if chkpt <= song_time]) - 1
            # time since the checkpoint
            offset = song_time - checkpoints[blknum]
            # fractional number of blocks passed.
            blkfrac = offset / (checkpoints[blknum+1] - checkpoints[blknum])
            blkpos = blknum + blkfrac

            my_messages.append(MyMessage(msg, blkpos))
            song_time += msg.time


    # correct the time of each message
    # overwrite the previous messages
    # iterate over pairs to work out what the correct gap needs to be

    # THIS IS INACCURATE you will get rounding errors over time!

    for my_msg0, my_msg1 in zip(my_messages, my_messages[1:]):
        my_msg0.msg.time = \
            mido.second2tick(my_msg1.blkpos * target_blklen, mid.ticks_per_beat, tempo) - \
            mido.second2tick(my_msg0.blkpos * target_blklen, mid.ticks_per_beat, tempo)

        # my_msg0.msg.time = (my_msg1.blkpos - my_msg0.blkpos) * target_blklen

    # convert the last msg to int
    my_messages[-1].msg.time = 100

    # corrected

    # input("\nFinished! Press enter to play")

    track = mid.tracks[0]

    # replace messages in the original mid
    for i, msg in enumerate(track):
        if type(msg) is mido.messages.messages.Message:
            # msg = my_messages.pop(0).msg
            # # need to convert to ticks here for some reason - not sure exactly when it gets converted to a time in seconds but we need to convert it back.
            # msg.time = int(msg.time * 120 * 8)
            # track[i] = msg
            track[i] = my_messages.pop(0).msg
    
    return mid