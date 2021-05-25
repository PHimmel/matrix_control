"""
A program for controlling LED matrices. Offers the ability to have continuous, autonomous operation
as well as a simple interface to rapidly switch to other settings/functions.

NOTES NOT ON RPI VERSION:

    # make scroll_weather more flexible, can be reused as a .sh for many other tasks

    The implementation layer is within the Bash class. All of the it's child classes only server to organize and
    create the flow of it's logic. They also offer a clear and concise interface for accessing specific functionality
    derived from Bash.

    Bash is mostly build off of the hzeller rpi-rgb-led-matrix library --> it's API
    is solely through the CLI, this is why Bash contains bash commands and interfaces with the terminal through the
    subprocess python-standard library.

    the actual running script is centralized in the main function.



    ### USE THE PYTHON BINDINGS TO BUILD OFF OF THE RBG LIBRARY!!!!
    ### NOW IT IS LARGELY SHELL SCRIPT
    ### MUST CHANGE :D

todo --> There should be an easy way to adjust main, persistent values (ie. rpi_rgb flags, graphics, etc)
todo --> otherwise it must be painstakingly done line-by-line :(
todo --> values that are used globally should be MADE GLOBAL

"""

from signal import signal, SIGTERM
from subprocess import call, Popen, DEVNULL
from os import popen
from sys import exit
from time import sleep
from datetime import datetime
from random import randint

import basic_scraper

# global variables
matrix_settings = ' --led-cols=64 --led-rows=64 --led-chain=4 --led-parallel=2 --led-pwm-bits=6 --led-slowdown-gpio=8' \
                  ' --led-pwm-lsb-nanoseconds=100 -f ../fonts/PETERS_FONTS/joystix_17.bdf --led-brightness=80 '
clock_position = 'I:%M:%S_%p -x15 -y27'

led_example_directory_path = '/home/pi/Matrix/ArduinoOnPc-FastLED-GFX-LEDMatrix/rpi-rgb-led-matrix/examples-api-use'
text_cmd = 'scrolling-text-example'


class Bash:

    def __init__(self):
        self.get_weather = 'WEATHER=$(curl wttr.in/13413?format="%C+%t+%hRH")'

        self.scroll_weather = 'sudo ./{} $WEATHER -y25 -s3 -l2 -C50,127,168{}'.format(text_cmd, matrix_settings)

        self.scroll_news = 'sudo ./{} $NEWS -B21,17,122 -C201,64,10 -y24 -s6 -l1{}'.format(text_cmd, matrix_settings)

        self.text = 'sudo ./{} 30 Minute Update! -s3 -y24 -B200,10,53 -l2{}'.format(text_cmd, matrix_settings)

        self.stop_matrix = 'ps -ef|grep led | grep -v grep | awk \'{print $2}\'| sudo xargs kill'
        self.stop_matrix = 'ps -ef|grep led | grep -v grep | awk \'{print $2}\'| sudo xargs kill'

    @staticmethod
    def _call(command):
        call('{} > /dev/null 2>&1'.format(command), cwd=led_example_directory_path, shell=True)

    @staticmethod
    def _popen(command):
        Popen(command.split(' '), cwd=led_example_directory_path, stdout=DEVNULL)

    @staticmethod
    def two_commands(one, two):
        call('{} > /dev/null 2>&1 ; {} > /dev/null 2>&1'.format(one, two), cwd=led_example_directory_path, shell=True)

    def kill_matrix(self):
        self._call(self.stop_matrix)

    def clock(self, settings):
        self._popen(settings)

    def weather(self):
        self.two_commands(self.get_weather, self.scroll_weather)

    def scrolling_text(self):
        self._call(self.text)

    #   def set_envir_var(self, name, data):
    #   self._call('{}={}'.format(name, data))

    def news_headlines(self, bash_env_name, data):
        set_var = '{}=\"BBC: {}\"'.format(bash_env_name, data)
        self.two_commands(set_var, self.scroll_news)

    def demo_number(self, number, time):
        self._call('bash -c \'sleep {} && sudo pkill -f demo\' &'.format(time))
        self._call('sudo ./demo -D{}{}-m 45'.format(number, matrix_settings[0:-60]))

    # used for control of a solid state relay to power the display
    @staticmethod
    def power_supply():
        state = popen('gpio read 29').read()
        if state.strip() == '1':
            return
        popen('gpio mode 29 out ; gpio write 29 1')


"""
Clock offers user-specified default settings for the operation of an on-going clock display.
"""


class Clock(Bash):
    single_clock = 'sudo ./clock -d %-1{}{}'.format(clock_position, matrix_settings)
    double_clock = 'sudo ./clock -d %{}{}'.format(clock_position, matrix_settings)

    # nice ASCII --->   » ‗ ┼

    def __init__(self, regular_night=False):
        super().__init__()
        self.message = Message()
        self.headlines = None
        self.target_minute = 15
        self.target_hour = 9
        self.hour, self.minute, self.second = get_current_hour_minute_second()
        self.regular_night = regular_night
        self.nightClock = False

    # sets clock formatting based on number of positions required
    def set_clock(self, settings):
        if 0 < self.hour < 10 or 12 < self.hour < 22:
            if self.nightClock is False:
                self.clock(Clock.single_clock + settings)
            else:
                self.clock(Clock.single_clock[0:-20] + settings)
            return

        if self.nightClock is False:
            self.clock(Clock.double_clock + settings)
        else:
            self.clock(Clock.single_clock[0:-20] + settings)

    def night_clock(self):
        self.kill_matrix()
        self.nightClock = True

        self.set_clock('-C 115,50,122 --led-brightness=30 ')
        self.set_sleep_till_hour()

    def set_sleep(self):
        # process start time
        start_secs = self.minute * 60 + self.second
        # current time
        now_secs = datetime.now().minute * 60 + datetime.now().second
        # time elapsed during process
        start_secs = now_secs - start_secs
        # total time until wake
        target_secs = self.target_minute * 60
        # seconds between process start and wake (ULTIMATELY ROUNDS TO THE NEAREST MINUTE)
        difference = target_secs - start_secs
        # sleep occurs in this method
        sleep(difference)

    def set_sleep_till_hour(self):
        till_hour = self.target_hour - self.hour - 1

        if till_hour < 0:
            till_hour = 24 - self.hour + self.target_hour - 1

        sleep_secs = (till_hour * 3600) + ((60 - self.minute) * 60)
        sleep(sleep_secs)

    def set_first_sleep(self):
        minutes = [m for m in range(self.minute, self.minute + self.target_minute) if m % self.target_minute == 0]

        if int(minutes[0]) - 1 <= 0:
            minutes += self.target_minute

        target_minutes = int(minutes[0]) - self.minute
        target_seconds = 60 - self.second

        slumber = (target_minutes - 1) * 60 + target_seconds
        if slumber < 0:
            slumber = target_seconds
        sleep(slumber)

    def set_rand_color_clock_and_sleep(self):
        self.nightClock = False
        self.set_clock(rand_color())
        self.set_sleep()

    # set to display messages at the top of each hour during the day ---takes n headlines from main list to display,
    # deletes after for continuous new headline ticker if it runs through the total list - a new list is generated

    def run_messages_with_headlines(self):
        if len(self.headlines) != 0:
            try:
                self.message.run_messages(' >>> '.join(self.headlines[0:5]))
                del (self.headlines[0:5])
            except IndexError:
                self.update_headlines_and_run_messages()
        else:
            self.update_headlines_and_run_messages()

    def get_headlines(self):
        self.headlines = basic_scraper.get_headlines()
        return self.headlines

    def update_headlines_and_run_messages(self):
        self.get_headlines()
        self.run_messages_with_headlines()

    def run_messages_without_headlines(self):
        pass

    # This method currently serves as main for running the clock/total based on time. Bash.kill_matrix() is needed
    # immediately after any clock display. All other matrix commands clear themselves after 1) time expiration 2)
    # data served fully. The clock is a continuous daemon that must be explicitly turned off before anything can be
    # displayed. Failure to do so will result in a completely unresponsive/error-state matrix the matrix requires
    # at least ~3 seconds of sleep between one command and one immediately afterwards

    def run_clock(self):
        try:
            # get list of all h3 (main) headline titles from BBC news
            self.get_headlines()
            start = True

            while True:
                self.hour, self.minute, self.second = get_current_hour_minute_second()

                # initialization
                if start is True:
                    # check SMPS state ; if off ; then turn on
                    Bash.power_supply()

                    self.set_clock(rand_color())
                    start = False
                    self.set_first_sleep()
                    continue

                # night settings
                if self.regular_night is True:
                    if self.hour > 21 or self.hour <= self.target_hour:
                        self.night_clock()
                        continue
                else:
                    if 2 < self.hour <= self.target_hour:
                        self.night_clock()
                        continue

                # day settings
                if self.minute % 30 == 0:
                    self.kill_matrix()

                    Graphics().demo_number(10, 20)
                    self.kill_matrix()
                    self.run_messages_with_headlines()

                    # run specific demo for fixed period of time
                    Graphics().demo_number(9, 30)
                    self.kill_matrix()

                    self.set_rand_color_clock_and_sleep()
                    continue

                elif self.minute % self.target_minute == 0:
                    self.kill_matrix()

                    self.set_rand_color_clock_and_sleep()
                    continue

                else:
                    continue

        # IDEA: add a goodbye message here
        except KeyboardInterrupt:
            self.kill_matrix()
            return


class Message(Bash):

    def __init__(self):
        super().__init__()

    # run_message is the 'main' method of Message.
    def run_messages(self, headlines):
        self.new_hour()
        self.display_weather()
        self.news(headlines)

    def display_weather(self):
        self.weather()

    def new_hour(self):
        self.scrolling_text()

    def news(self, headlines):
        self.news_headlines('NEWS', headlines)


class Graphics(Bash):
    def __init__(self):
        super().__init__()

    def demo(self, number, time):
        self.demo_number(number, time)


class Image:
    pass


class Terminate:

    def __init__(self):
        self.received = False
        signal(SIGTERM, self.receive)

    def receive(self):
        self.received = True


def get_current_hour_minute_second():
    now = datetime.now()
    return now.hour, now.minute, now.second


def rand_num():
    x = 0
    ls = []
    while x < 3:
        ls.append(randint(0, 255))
        x += 1
    return str(ls).strip('[]').replace(' ', '')


def rand_color():
    return '-C {} -B {} -O 0,0,0 '.format(rand_num(), rand_num())


def kill_power():
    popen('gpio write 29 0')
    exit()


def main():
    terminate = Terminate()
    while not terminate.received:
        try:
            clock = Clock()
            clock.run_clock()
        except TypeError:
            kill_power()
        finally:
            kill_power()
    kill_power()


if __name__ == '__main__':
    main()
else:
    print('Imported')
