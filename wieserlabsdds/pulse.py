"""
The purpose of this code is to provide a library to send arbitrary pulses to the DDS.
This class automatically optimizes the placement of the update.

"""

from . import wieserlabsdds
from numpy import pi


class Pulse:
    """
    This class represents a Pulse
    """

    def __init__(self, freq:float, amp:float, phase:float, t:float):
        """
        A class representing a pulse on the DDS.

        Parameters
        ----------
        freq : float
            Frequency of the pulse in Hz
        amp : float
            The amplitude of the pulse. Has to be 0<=amp<=1.
        phase : float
            The phase of the pulse in deg, not rad.
        t : float
            The duration of the pulse in seconds.
        """

        self.freq = freq
        self.amp = amp
        self.phase = phase
        self.t = t

    def __str__(self):
        return "Pulse with freq %.2fMHz, amp of %d%% and phase=%d° for %.3es" % (self.freq*1e-6, self.amp*100, self.phase, self.t)


class XPulse(Pulse):
    """
    This class represents an X-Pulse
    """

    def __init__(self, freq:float, amp:float, t:float):
        """
        A class representing an X pulse.

        Parameters
        ----------
        freq : float
            Frequency of the pulse in Hz
        amp : float
            The amplitude of the pulse. Has to be 0<=amp<=1.
        t : float
            The duration of the pulse in seconds.
        """
        super().__init__(freq, amp, 0, t)

    def __str__(self):
        return "X Pulse for %.3es with freq %.2fMHz and amp of %d%%" % (self.t, self.freq*1e-6, self.amp*100)

class YPulse(Pulse):
    """
    This class represents a Y-Pulse
    """

    def __init__(self, freq:float, amp:float, t:float):
        """
        A class representing a Y pulse.

        Parameters
        ----------
        freq : float
            Frequency of the pulse in Hz
        amp : float
            The amplitude of the pulse. Has to be 0<=amp<=1.
        t : float
            The duration of the pulse in seconds.
        """
        super().__init__(freq, amp, 90, t)

    def __str__(self):
        return "Y Pulse for %.3es with freq %.2fMHz and amp of %d%%" % (self.t, self.freq*1e-6, self.amp*100)




class PulseSequence:
    """
    A pulse sequence for the DDS.

    This class optimizes the loading of the pulse information to achieve a pulse length accuracy on the order of 100ns.
    """

    def __init__(self, dds, slot:int, channel:int, default_freq:float=1e6, default_amp:float=1):
        """
        Pulse sequence for the DDS

        The idea is, that you can add arbitrary pulses to this sequence and upon compiling the wait and update statements for the DDS will be inserted automatically.
        Thus this class makes it easy, to send pulses to the DDS.

        Parameters
        ----------
        dds : WieserlabsClient
            An instance of :class:'wieserlabsdds.wieserlabsdds.WieserlabsClient' to send the pulses to.
        slot : int
            Frequency of the pulse in Hz
        channel : int
            The amplitude of the pulse. Has to be 0<=amp<=1.
        default_freq : float
            The default frequency in Hz to be used, if no other frequency is given
        default_amp : float
            The default amplitude between 0 and 1 to be used, if no other amplitude is given
        """
        self.dds = dds
        self.slot = slot
        self.slot = channel
        self.default_freq = default_freq
        self.default_amp = default_amp

        self.pulses = []
        self.generated = False

    def add_pulse(self, t:float, freq:float=None, amp:float=None, phase:float=0):
        """
        Adds a pulse with duration t to the sequence
        """
        if freq == None: freq = self.default_freq
        if amp == None: amp = self.default_amp
        self.pulses.append(Pulse(freq, amp, phase, t))

    def generate(self, trigger_option=1, trigger=[wieserlabsdds.TriggerEvent.BNC_IN_A_RISING]):
        """
        Generate the pulse sequence while lading pulse data during wait times to achieve an optimal timing.

        Parameters
        ----------

        trigger_option: int
            An option to choose how to start and run the sequence.
            If 0 is selected, the sequence will run by executing this command.
            This does not allow for a precise start time, since the sequence will just run once it is transmitted to the DDS.

            If 1 is selected, the DDS will wait for an initial trigger, given by the trigger argument. The rest of the timing is done by the DDS itself.

            If 2 is selected, a trigger for every pulse is inserted.
            This way, you can externally control the timing of the pulses.
            In this case, the duration argument of the pulses will not be used.
        
        trigger : list
            A list containing the number of trigger events this pulse sequence listens to. Those trigger events should be chosen from the enum defined in :class:`wieserlabsdds.wieserlabsdds.TriggerEvent`.
        """
        # put pulses on DDS
        if self.generated:
            print("WARNING!! If you call the generate method multiple times, you will execute the pulse sequence twice!\nThis will most likely lead to unexpected behaviour!")

        if len(self.pulses) == 0:
            print("WARNING: you called the generate function without having provided any pulses.\nNothing will be sent to the DDS.")
            return

        p = self.pulses[0]
        # put first pulse in the sequence on the DDS
        self.dds.single_tone(self.slot, self.channel, freq=p.freq, amp=p.amp, phase=p.phase, suffix=None if trigger_option == 0 else "c")
        if trigger_option == 0:
            # update to start this pulse
            self.dds.push_update(self.slot, self.channel)
        else:
            # in any other case, we need to wait for the trigger, until we can apply the single-tone
            self.dds.wait_trigger(self.slot, self.channel, trigger, update_before_wait=False)
            self.dds.push_update(self.slot, self.channel)


        # generate the pulse sequence:
        for i in range(len(self.pulses)):
            p = self.pulses[i]
            self.dds.single_tone(self.slot, self.channel, freq=p.freq, amp=p.amp, phase=p.phase, suffix="c") # add c for the next pulse to be loaded while the previous is still active
            self.dds.wait_time(self.pulses[i-1].t, update_before_wait=False) # do not push an update, we already pre-loaded the data and want to keep it there, until the wait is over
            self.dds.push_update(self.slot, self.channel)   # update, now that the wait time is over


        # finally, wait for the duration of the last pulse and turn off afterwards
        self.dds.single_tone(self.slot, self.channel, freq=p.freq, amp=0, phase=p.phase, suffix="c") # set the amplitude to 0 to "turn off" the signal
        self.dds.wait_time(self.pulses[-1].t, update_before_wait=False)
        self.dds.push_update(self.slot, self.channel)

        self.generated = True


    def run(self):
        """
        Upload the sequence to the DDS and run it
        """
        if not self.generated: self.generate()
        self.dds.run(self.slot)


    def __str__(self):
        res = "This is a pulse sequence consisting of\n"
        for p in self.pulses:
            res += str(p) + "\n"
        return res


    


class QubitPulseSequence(PulseSequence):
    """
    A pulse sequence for the DDS.

    This class is intended to perform qubit rotations and thus a specialization from the more general :class:`PulseSequence` class.
    """

    def __init__(self, dds, slot:int, channel:int, pi_pulse_time:float, freq:float=1e6, amp:float=1):
        """
        Pulse sequence for the DDS

        Parameters
        ----------
        dds : wieserlabsdds.WieserlabsClient
            An instance of :class:`wieserlabsdds.wieserlabsdds.WieserlabsClient` to send the pulses to. 
        slot : int
            Frequency of the pulse in Hz
        channel : int
            The amplitude of the pulse. Has to be 0<=amp<=1.
        pi_pulse_time : float
            The time in seconds, it takes for a pi rotation around the X axis.
        freq : float
            The default frequency in Hz to be used, if no other frequency is given
        amp : float
            The default amplitude between 0 and 1 to be used, if no other amplitude is given
        """
        super().__init__(dds, slot, channel, freq, amp)
        self.freq = freq
        self.amp = amp
        self.pi_pulse_time = pi_pulse_time

    def _angle_to_time(self, theta:float):
        """
        Converts an angle into time by using the given pi pulse time.

        theta : float
            rotation angle in rad.
        """
        return theta/pi * self.pi_pulse_time

    def add_pulse(self, phi:float, theta:float):
        """
        Adds a pulse around the axis given by phi with the angle theta.
        
        phi : float
            angle of the rotation axis in the X-Y-plane in rad.
            phi=0 corresponds to a pure X pulse and phi=pi/2 to a pure Y pulse
        theta : float
            rotation angle in rad. Pretty self-explanatory, the angle for which we rotate
        """
        self.pulses.append(Pulse(self.freq, self.amp, phi/pi*180, self._angle_to_time(theta)))

    def add_x_pulse(self, theta:float):
        """
        Adds an X rotation with the angle theta to the sequence

        theta : float
            rotation angle in rad.
        """
        self.pulses.append(XPulse(self.freq, self.amp, t=self._angle_to_time(theta)))

    def add_y_pulse(self, theta:float):
        """
        Adds a Y rotation with the angle theta to the sequence

        theta : float
            rotation angle in rad.
        """
        self.pulses.append(YPulse(self.freq, self.amp, t=self._angle_to_time(theta)))

    