#!venv/bin/python

import threading
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import messagebox

from Player import Player
from spacer import space_notes
import mido
import webbrowser

port = mido.open_output()


heading_font = ("sans serif", 20, "bold") 

# create window
root = tk.Tk()
root.title("Midi Spacer")
# root.geometry('600x400')


class MainMenu(tk.Frame):
    def __init__(self, parent : tk.Misc):
        tk.Frame.__init__(self, parent, padx=20, pady=20)

        self.input_file_set : bool = False

        l0 = tk.Frame(self)
        tk.Label(l0, text="Instructions", font=heading_font).grid(row=0, column=0)
        tk.Label(l0, text="""1. Click the link below to follow instructions on converting a Garageband region to a MIDI file.""").grid(row=1, column=0)
        link1 = tk.Label(l0, text="https://producersociety.com/how-to-export-midi-from-garageband/", fg="#99F", cursor="hand2")
        link1.grid(row=2, column=0)
        link1.bind("<Button-1>", lambda e: webbrowser.open_new("https://producersociety.com/how-to-export-midi-from-garageband/"))
        tk.Label(l0, text="""2. Select the MIDI file using the Choose button.
3. Edit any settings if needed.
4. Click Next.""").grid(row=3, column=0)
        l0.grid(column=0, row=0)

        # line 1
        l1 = tk.Frame(self)
        # place label on window
        tk.Label(l1, text="Input MIDI file location", font=heading_font).pack()
        l1.grid(column=0, row=1, pady=(10,0))

        l2 = tk.Frame(self)
        self.choose_btn = tk.Button(l2, text="Choose", command=self.choose_file)
        self.choose_btn.grid(column=0, row=0)
        self.selected_loc_var = tk.StringVar(self, "No file selected")
        self.selected_loc_label = tk.Label(l2, textvariable=self.selected_loc_var)
        self.selected_loc_label.grid(column=1, row=0)
        l2.grid(column=0, row=2)

        l3 = tk.Frame(self)
        tk.Label(l3, text="Settings", font=heading_font).pack()
        l3.grid(column=0, row=3, pady=(10, 0))

        l4 = tk.Frame(self)
        tk.Label(l4, text="Target tempo: ").grid(row=0, column=0)
        self.tempo_entry = tk.Entry(l4, width=5)
        self.tempo_entry.insert(0, "120")
        self.tempo_entry.grid(row=0, column=1)
        tk.Label(l4, text="bpm").grid(row=0, column=2)
        l4.grid(column=0, row=4)

        l5 = tk.Frame(self)
        tk.Label(l5, text="Checkpoint every").grid(row=0, column=0)
        self.checkpoint_freq_entry = tk.Entry(l5, width=5)
        self.checkpoint_freq_entry.insert(0, "2")
        self.checkpoint_freq_entry.grid(row=0, column=1)
        tk.Label(l5, text="beats").grid(row=0, column=2)
        l5.grid(column=0, row=5)

        l6 = tk.Frame(self)
        self.next_button = tk.Button(l6, text="Next", command=lambda: self.next())
        self.next_button.grid(row=0, column=0)
        l6.grid(column=0, row=6, pady=(10,0))
    
    def next(self):
        """Validate user input, then if successful open the next window.
        """

        # verify that the user has entered things corrently
        valid = True
        errors = []
        # check tempo is an integer
        bpm = None
        try:
            bpm = int(self.tempo_entry.get())
        except ValueError:
            errors.append("Tempo is not an integer")
            valid = False
        else:
            if bpm <= 0:
                errors.append("Tempo is not positive")
                valid = False
        
        # check that checkpoint frequency is positive
        freq = None
        try:
            freq = float(self.checkpoint_freq_entry.get())
        except ValueError:
            errors.append("Checkpoint frequency is not a number")
            valid = False
        else:
            if freq <= 0:
                errors.append("Checkpoint frequency is not positive")
                valid = False
        
        # check that the user has seleted a midi file for input
        if not self.input_file_set:
            errors.append("Please choose an input midi file")
            valid = False
        
        # todo should also probably che ck to see if it is a valid midi file or not

        if not valid:
            if len(errors) == 1:
                messagebox.showwarning(self, message=errors[0])
            else:
                messagebox.showwarning(self, message="There are multiple problems:\n" + "\n".join(errors))
            return

        # open the midi file
        try:
            mid = mido.MidiFile(self.selected_loc_var.get())
        except:
            messagebox.showerror(self, "Unable to open the midi file at location " + self.selected_loc_var.get())
            raise

        # pass stuff to the RecordWindow
        RecordWindow(self, mid, bpm, freq)
    

    def choose_file(self):
        """Prompt the user to select a MIDI file and store the result if they do not cancel.
        """
        filename = fd.askopenfilename(defaultextension="mid", filetypes=[("MIDI file", [".mid", ".MID", ".midi"])])
        if filename is None or filename == "" or filename == ():
            return
        self.selected_loc_var.set(filename)
        self.input_file_set = True

        print(filename)


class RecordWindow(tk.Toplevel):
    """Window for the recording screen.
    """
    def __init__(self, parent: tk.Misc, mid : mido.MidiFile, bpm: int, freq: float):
        tk.Toplevel.__init__(self, parent)

        self.mid = mid
        self.bpm = bpm
        # self.blklen = blklen
        self.freq = freq
        self.time_signature = (4,4)
        self.port = port
        self.player : Player | None = None

        # line 1
        l1 = tk.Frame(self)
        # place label on window
        tk.Label(l1, text="Instructions", font=heading_font).pack()
        l1.grid(column=0, row=0)

        l2 = tk.Frame(self)
        # place label on window
        tk.Label(l2, text="""1. Make sure that Garageband is open to a project and that you can hear audio when pressing the "Test Audio" button.
2. Get ready to add checkpoints - you will be able to do this by pressing the large "Add Checkpoint" button below, or by tapping the spacebar.
3. Click "Begin" to start the audio playing.""").pack()
        l2.grid(column=0, row=1)

        l3 = tk.Frame(self)
        self.begin_button_var = tk.StringVar(self, "")
        self.begin_button = tk.Button(l3, textvariable=self.begin_button_var, command=self.begin_cancel_clear)
        self.begin_button.grid(row=0, column=0)
        tk.Button(l3, text="Test Audio", command=self.test_audio).grid(row=0, column=1)
        self.save_button = tk.Button(l3, text="Save", state="disabled", command=self.save)
        self.save_button.grid(row=0, column=2)
        l3.grid(column=0, row=5)

        self.set_begin_cancel_clear("Begin")


        l4 = tk.Frame(self, borderwidth=2, background="gray")
        self.add_chkpt = tk.Button(l4, text="Add Checkpoint (space)", font=heading_font, background="#FF0000", padx=10, pady=10, command=self.add_checkpoint)
        self.add_chkpt.grid(row=0, column=0, padx=150)
        self.log = tk.Label(l4)
        self.log.grid(column=1, row=0)
        l4.grid(column=0, row=6)




        self.bind('<space>', lambda event: self.add_checkpoint())

        self.checkpoints = [0.0]
        self.render_checkpoints()

    def add_checkpoint(self):
        """Add a checkpoint at the current time of the Player
        """

        if self.player is not None:
            self.checkpoints.append(self.player.get_time())

            # terminate the player if it has finished
            if not self.player.playing:
                self.player.join()
                self.set_begin_cancel_clear("Clear")
                self.player = None

            self.render_checkpoints()
    

    def begin_cancel_clear(self):
        """Called when the begin/cancel/clear button is pressed. Performs the correct function and changes the value of the button."""
        if self.begin_button_var.get() == "Begin":
            self.start_playback()
            self.set_begin_cancel_clear("Cancel")
        elif self.begin_button_var.get() == "Cancel":
            self.cancel_playback()
            self.set_begin_cancel_clear("Clear", save_button_new_state="disabled")
        elif self.begin_button_var.get() == "Clear":
            self.clear()
            self.set_begin_cancel_clear("Begin")

    def set_begin_cancel_clear(self, new_val, save_button_new_state=None):
        """Set the state of the Begin/Cancel/Clear button. Also changes the state of the button, and the state of the Save button,

        Args:
            new_val ("Begin" | "Cancel" | "Clear"): New value of the Begin/Cancel/Clear button.
            save_button_new_state ("normal" | "disabled" | "active" | None, optional): Override the automatic state of the save button. Defaults to None.
        """
        self.begin_button_var.set(new_val)

        # state of button ()
        self.begin_button.config(state="active" if new_val == "Begin" else "normal")

        # also change the state of the save button.
        if save_button_new_state is None:
            save_button_new_state = "active" if new_val == "Clear" else "disabled" 
        
        self.save_button.config(state=save_button_new_state)


    def start_playback(self):
        """Creates a new Player thread and starts playing the selected midi file.
        """
        self.player = Player(self.mid, self.port)
        self.player.start()
    
    def test_audio(self):
        self.port.send(mido.Message("note_on", note=60, time=0.2))
        self.port.send(mido.Message("note_off", note=60))
        # pass

    def cancel_playback(self):
        """Stops the player thread.
        """

        if self.player is not None:
            # breaks out of loop in the player thread
            self.player.playing = False

            # fixme this might cause the ui to hang until the start of the next note.
            self.player.join()
            self.player = None
    

    def clear(self):
        """Clears all checkpoints and creates a new checkpoint 0.
        """
        self.checkpoints = [0.0]
        self.render_checkpoints()

    def save(self):
        """Procedure for saving to a midi file. Spaces the notes, prompts the user for a place to save, then saves.
        """
        # do the spacing
        blklen = self.freq/self.bpm * 60
        try:
            spaced_mid = space_notes(blklen, self.mid, self.checkpoints, mido.bpm2tempo(self.bpm, self.time_signature))
        except:
            messagebox.showerror("Failed to space notes")
            raise

        # get location to save the file
        loc_wrapper = fd.asksaveasfile(initialfile="untitled.mid", defaultextension="mid", filetypes=[("MIDI File", [".mid", ".MID", ".midi"])])

        if loc_wrapper is None:
            return
        
        loc = loc_wrapper.name
        
        try:
            spaced_mid.save(loc)
        except:
            messagebox.showerror("Failed to save file")
            raise




    def render_checkpoints(self):
        """Re-creates the list of checkpoints on screen.
        """

        max_to_display = 10

        # display the last 10
        start_at = max(len(self.checkpoints)-max_to_display, 0)
        lines = [""] * max_to_display
        for i, cp in enumerate(self.checkpoints[start_at:]):
            lines[i] = f"Checkpoint {start_at+i}: {cp:.3f} seconds"
        
        # replace first line with elipsis if there are too many to fit on the screen
        if i == max_to_display-1:
            lines[0] = "..."
      
        self.log.config(text="\n".join(lines))



main_menu = MainMenu(root)
main_menu.pack()


root.mainloop()