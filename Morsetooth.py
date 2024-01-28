#!/usr/bin/python
# -*- coding: utf-8 -*-

from microbit import display, button_a, button_b, pin1, sleep
from radio import on, config, receive, send
import music


DEFAULT_SCROLL_DELAY = 200
DEFAULT_CHANNEL = 25
DEFAULT_POWER = 7
DEFAULT_SEPERATOR = "_:_"

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
    ", ": "--..--",
    ".": ".-.-.-",
    "?": "..--..",
    "/": "-..-.",
    "-": "-....-",
    "(": "-.--.",
    ")": "-.--.-",
}


def get_channel(len: int = 5):
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
        "Set channel",
        loop=True,
        wait=False,
        delay=DEFAULT_SCROLL_DELAY,
    )
    binary = []

    # If the first binary number is 0, set channel to `DEFAULT_CHANNEL`
    # (default: 25)
    while True:
        if button_a.was_pressed():
            return DEFAULT_CHANNEL
        elif button_b.was_pressed():
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
    # Set channel to `channel` and power level to `DEFAULT_POWER`
    # (default: 7)
    config(group=channel, power=DEFAULT_POWER)

    display.clear()
    display.scroll(channel, delay=DEFAULT_SCROLL_DELAY)


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

    # Add extra space to the input to mark its end
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

            # Two consecutive spaces mean a new word
            if spaces == 2:
                # Add space to indicate the end of the word
                decipher += " "
                spaces = 0
            else:
                try:
                    # Access the keys using their values
                    decipher += list(MORSE_DICT.keys())[
                        list(MORSE_DICT.values()).index(word)
                    ]
                except ValueError:
                    return input_

                word = ""

    return decipher if decipher != "" else input_


if __name__ == "__main__":
    setup_radio()

    queue = []

    currently_pressing_a_b = False
    local_message = ""
    while True:
        # Turn off an eventual unit connected to pin 1, most probably a lamp
        if display_empty() and pin1.is_touched():
            pin1.write_digital(0)

        received_data = get_data()  # Receives data on `channel`
        if received_data:
            queue.append(received_data)
        if queue and display_empty():
            # Seperate all messages with `DEFAULT_SEPERATOR` (default:
            # "_:_")
            message = str(morse_decipher(queue[0])) + DEFAULT_SEPERATOR
            # The display can never be empty, since that would trigger
            # `display_empty()`, allowing for another message to replace
            # the current one. Therefore, we have to replace all spaces
            # with underscores (_).
            message = message.replace(" ", "_")

            # Turn on an eventual light on pin 0
            if pin1.is_touched():
                pin1.write_digital(1)

            music.play(music.JUMP_UP, wait=False)

            display.scroll(
                message,
                wait=False,
                delay=DEFAULT_SCROLL_DELAY,
            )
            queue.pop(0)

        # If A and B are pressed, add " " to message
        if button_a.is_pressed() and button_b.is_pressed():
            currently_pressing_a_b = True
            local_message += " "
        # If A is pressed, add "." to message
        elif button_a.was_pressed():
            local_message += "."
            display.scroll(":" + local_message + ":")
        # If B is pressed, add "-" to message
        elif button_b.was_pressed():
            local_message += "-"

        if (
            not button_a.is_pressed()
            and not button_b.is_pressed()
            and currently_pressing_a_b
        ):
            currently_pressing_a_b = False

        # If A and B are pressed three times in a row, send message
        if local_message[-3:] == 3 * " ":
            music.play(music.JUMP_DOWN, wait=False)
            send(local_message[:-3])
            local_message = ""
