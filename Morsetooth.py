#!/usr/bin/python
# -*- coding: utf-8 -*-

from microbit import display, button_a, button_b, pin1, sleep
from radio import on, config, receive, send
from music import play
import music

DEFAULT_SCROLL_DELAY_MS = 200  # Range: 0-
DEFAULT_CHANNEL_LEN = 5  # Range 1-7
DEFAULT_CHANNEL = 25  # Range: 0-255
DEFAULT_POWER = 7  # Range: 1-7
DEFAULT_SEPARATOR = "_:_"
DEFAULT_TICK_MS = 100  # Range: 0-
USE_LIGHTS = True
USE_MUSIC = True
DEFAULT_MSG_RECEIVED_TUNE = music.JUMP_UP
DEFAULT_MSG_SENT_TUNE = music.JUMP_DOWN
MORSE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "AA": ".--.-",
    "AE": ".-.-",
    "OE": "---.",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "0": "-----",
    ",": "--..--",
    ".": ".-.-.-",
    "?": "..--..",
    "/": "-..-.",
    "-": "-....-",
    "(": "-.--.",
    ")": "-.--.-",
}


def get_channel(len: int = DEFAULT_CHANNEL_LEN):
    """
    Gets radio channel from user input. Allows for binary input (A: 0, B:
    1) with length `len` (default: 5). If the first binary input is A,
    the channel is set to the default value `DEFAULT_CHANNEL` (default:
    25).

    :param len: Length of the channel binary
    :type len: int
    :returns: The channel in decimal form
    :rtype: int
    """

    display.scroll(
        "SET CHANNEL",
        loop=True,
        wait=False,
        delay=DEFAULT_SCROLL_DELAY_MS,
    )
    binary = []

    # If the first binary number is 0, set channel to `DEFAULT_CHANNEL`
    # (default: 25)
    while True:
        if button_a.was_pressed():
            return DEFAULT_CHANNEL
        elif button_b.was_pressed():
            # Stop the scrolling "SET CHANNEL" message by replacing it with nothing
            display.scroll("")
            break

    for _ in range(len):
        while True:
            if button_a.was_pressed():
                bit = 0
                break
            elif button_b.was_pressed():
                bit = 1
                break

        binary.append(str(bit))
        display.show(bit)

    # Convert binary input to decimal
    binary_string = "".join(binary)
    return int(binary_string, 2)


def setup_radio():
    """Sets up the radio channel according to user input"""
    on()  # Activate the radio
    channel = get_channel()
    # Set channel to `channel` and power level to `DEFAULT_POWER` (default: 7)
    config(group=channel, power=DEFAULT_POWER)

    display.clear()
    display.scroll(channel, delay=DEFAULT_SCROLL_DELAY_MS)


def get_data():
    """Receives data from channel `channel`"""
    data = receive()
    if data:
        return data


def display_empty(width: int = 5, height: int = 5):
    """
    Checks if the display currently is empty

    :param width: The width of the display
    :type width: int
    :param height: The height of the display
    :type height: int
    :returns:
        - True - If the screen is empty
        - False - If the screen isn't empty
    :rtype: bool
    """

    for x in range(width):
        for y in range(height):
            if display.get_pixel(x, y):
                return False

    return True


def morse_decipher(input_: str):
    """
    Deciphers morse input into plain text

    :param input_: The input
    :type input_: str
    :returns: The deciphered text if it can be deciphered, if not, it will return the
    input as is
    :rtype: str
    """

    # If the input contains anything other than ".", "-", and
    # " ", return the input
    if all(char not in input_ for char in [".", "-"]):
        return input_

    # Add extra space to input to mark its end
    input_ += " "

    decipher = ""
    word = ""
    spaces = 0
    for char in input_:
        # Check for space
        if char != " ":
            spaces = 0
            # Add character to word
            word += char

        # Space found
        else:
            # Increment space amount by one
            spaces += 1

            # Two consecutive spaces means a new word
            if spaces == 2:
                # Add space to indicate the end of the word
                decipher += " "
                spaces = 0
            else:
                try:
                    # Access the keys using their values, and add the deciphered result to the deciphered text
                    decipher += list(MORSE_DICT.keys())[
                        list(MORSE_DICT.values()).index(word)
                    ]
                except ValueError:
                    pass
                except:
                    return input_

                word = ""

    return decipher


if __name__ == "__main__":
    setup_radio()

    queue = []

    local_message = ""
    while True:
        # Turn off an eventual unit connected to pin 1, most probably a lamp
        if USE_LIGHTS and display_empty():
            pin1.write_digital(0)

        received_data = get_data()  # Receives data on `channel`
        if received_data:
            queue.append(received_data)
        if queue and display_empty():
            # Turn on an eventual light on pin 0, if `USE`
            if USE_LIGHTS:
                pin1.write_digital(1)

            # Play chosen music, if `USE_MUSIC` is True
            if USE_MUSIC:
                play(DEFAULT_MSG_RECEIVED_TUNE, wait=False)

            # Separate all messages with `DEFAULT_SEPARATOR` (default:
            # "_:_")
            message = str(morse_decipher(queue[0])) + DEFAULT_SEPARATOR
            # The display can never be empty, since that would trigger
            # `display_empty()`, allowing for another message to replace
            # the current one. Therefore, we have to replace all spaces
            # with underscores (_).
            message = message.replace(" ", "_")

            display.scroll(
                message,
                wait=False,
                delay=DEFAULT_SCROLL_DELAY_MS,
            )
            queue.pop(0)

        # If A and B are pressed, add " " to message
        if button_a.is_pressed() and button_b.is_pressed():
            local_message += " "
            display.scroll("_ :" + morse_decipher(local_message) + ":", wait=False)
            sleep(2 * DEFAULT_TICK_MS)
        # If A is pressed, add "." to message
        elif button_a.is_pressed():
            char = "."
            local_message += char
            display.scroll(
                char + " :" + morse_decipher(local_message) + ":", wait=False
            )
            sleep(DEFAULT_TICK_MS)
        # If B is pressed, add "-" to message
        elif button_b.is_pressed():
            char = "-"
            local_message += char
            display.scroll(
                char + " :" + morse_decipher(local_message) + ":", wait=False
            )
            sleep(DEFAULT_TICK_MS)

        # If A and B are pressed three times in a row, send message
        if local_message[-3:] == 3 * " ":
            if USE_MUSIC:
                play(DEFAULT_MSG_SENT_TUNE, wait=False)
            send(
                local_message[:-3]
            )  # Send message minus the three last character (spaces)
            local_message = ""

        sleep(DEFAULT_TICK_MS)
