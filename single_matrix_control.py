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

todo --> There should be an easy way to adjust main, persistent values (ie. rpi_rgb flags, graphics, etc)
"""

from subprocess import call, Popen, DEVNULL
from time import sleep
from datetime import datetime
from random import randint
import basic_scraper


class Bash:

    def __init__(self):
        self.get_weather = 'WEATHER=$(curl wttr.in/13413?format="%C+%t+%hRH")'

        self.scroll_weather = 'sudo ./scrolling-text-example $WEATHER -f ../fonts/PETERS_FONTS/joystix_17.bdf ' \
                              '--led-cols=64 ' \
                              '--led-rows=64 --led-chain=4 --led-parallel=2 --led-slowdown-gpio=8 -y25 -s3 -l2 ' \
                              '-C50,127,168 '

        self.scroll_news = 'sudo ./scrolling-text-example $NEWS -f ../fonts/PETERS_FONTS/joystix_17.bdf ' \
                           '--led-pwm-bits=6 ' \
                           '--led-cols=64 --led-rows=64 --led-chain=4 --led-parallel=2 --led-slowdown-gpio=8 -B21,17,' \
                           '122 -C201,64,10 -y24 -s6 -l1 '

        self.text = 'sudo ./scrolling-text-example 30 Minute Update! -f ../fonts/PETERS_FONTS/joystix_17.bdf ' \
                    '--led-cols=64 --led-pwm-bits=6 ' \
                    '--led-rows=64 --led-chain=4 --led-parallel=2 --led-slowdown-gpio=8 -s3 -y24 -B200,10,53 -l2'

        self.stop_matrix = 'ps -ef|grep led | grep -v grep | awk \'{print $2}\'| sudo xargs kill'

        self.led_example_directory_path = '/home/pi/Matrix/ArduinoOnPc-FastLED-GFX-LEDMatrix/rpi-rgb-led-matrix' \
                                          '/examples-api-use'

    def _call(self, command):
        call('{} > /dev/null 2>&1'.format(command), cwd=self.led_example_directory_path, shell=True)

    def _popen(self, command):
        Popen(command.split(' '), cwd=self.led_example_directory_path, stdout=DEVNULL)

    def two_commands(self, one, two):
        call('{} > /dev/null 2>&1 ; {} > /dev/null 2>&1'.format(one, two), cwd=self.led_example_directory_path,
             shell=True)

    def kill_matrix(self):
        self._call(self.stop_matrix)

    def clock(self, settings):
        self._popen(settings)

    def weather(self):
        self.two_commands(self.get_weather, self.scroll_weather)

    def scrolling_text(self):
        self._call(self.text)

    #   def set_envir_var(self, name, data):
    #       self._call('{}={}'.format(name, data))

    def news_headlines(self, ENV_NAME, data):
        set_var = '{}=\"BBC: {}\"'.format(ENV_NAME, data)
        self.two_commands(set_var, self.scroll_news)

    def demo_number(self, number, time):
        print('made it')
        self._call('bash -c \'sleep {} && sudo pkill -f demo\' &'.format(time))
        self._call(
            'sudo ./demo -D{} --led-cols=64 --led-rows=64 --led-brightness=50 --led-pwm-lsb-nanoseconds=100 '
            '--led-chain=4 --led-pwm-bits=7 --led-parallel=2 --led-slowdown-gpio=8 -m 45'.format(
                number
            ))


"""
Clock offers user-specified default settings for the operation of an on-going clock display.
"""


class Clock(Bash):
    single_clock = 'sudo ./clock -f ../fonts/PETERS_FONTS/joystix_17.bdf -d %-1I:%M_%p --led-cols=64 --led-rows=64 ' \
                   '--led-chain=4 ' \
                   '--led-parallel=2 --led-slowdown-gpio=8 -x15 -y27 '
    double_clock = 'sudo ./clock -f ../fonts/PETERS_FONTS/joystix_17.bdf -d %I:%M%p --led-cols=64 --led-rows=64 ' \
                   '--led-chain=4 ' \
                   '--led-parallel=2 --led-slowdown-gpio=8 -x15 -y27 '

    # nice ASCII --->   » ‗ ┼

    def __init__(self):
        super().__init__()
        self.message = Message()
        self.headlines = None
        self.target_minute = 15
        self.target_hour = 9
        self.hour, self.minute, self.second = get_current_hour_minute_second()
        self.regular_night = False

    # sets clock formatting based on number of positions required
    def set_clock(self, settings):
        if 0 < self.hour < 10 or 12 < self.hour < 22:
            self.clock(Clock.single_clock + settings)
            return
        self.clock(Clock.double_clock + settings)

    def night_clock(self):
        self.kill_matrix()

        self.set_clock('-C 115,50,122 --led-brightness=2 ')
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
        minutes = [min for min in range(self.minute, self.minute + self.target_minute) if min % self.target_minute == 0]

        if int(minutes[0]) - 1 <= 0:
            minutes += self.target_minute

        target_minutes = int(minutes[0]) - self.minute
        target_seconds = 60 - self.second

        slumber = (target_minutes - 1) * 60 + target_seconds
        sleep(slumber)

    def set_rand_color_clock_and_sleep(self):
        self.set_clock(rand_color())
        self.set_sleep()

    # set to display messages at the top of each hour during the day ---takes n headlines from main list to display,
    # deletes after for continuous new headline ticker if it runsn through the total list - a new list is generated

    def run_messages_with_headlines(self):
        if len(self.headlines) != 0:
            try:
                self.message.run_messages(' >>> '.join(self.headlines[0:5]))
                del (self.headlines[0:5])
            except:
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
                    if 1 < self.hour <= self.target_hour:
                        self.night_clock()
                        continue

                # day settings
                if self.minute % 30 == 0:
                    self.kill_matrix()
                    Graphics().demo_number(10, 20)
                    self.run_messages_with_headlines()
                    # run specific demo for fixed period of time
                    Graphics().demo_number(9, 30)
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


def get_current_hour_minute_second():
    now = datetime.now()
    return now.hour, now.minute, now.second


def rand_color():
    return '-C {},{},{} -B {},{},{} -O 0,0,0 --led-brightness=60 '.format(randint(0, 255), randint(0, 255),
                                                                          randint(0, 255),
                                                                          randint(0, 255), randint(0, 255),
                                                                          randint(0, 255))


def main():
    clock = Clock()
    clock.run_clock()


if __name__ == '__main__':
    main()
else:
    print('Imported')
