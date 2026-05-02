"""Simple program to use voicevox with python."""

import logging.handlers
from contextlib import contextmanager
from pathlib import Path

import uvloop
from aiohttp import ClientSession

from voicevox import Voicevox

URL = "http://localhost:50021"


@contextmanager
def setup_logging():
    """Setups logging."""
    log = logging.getLogger()
    try:
        log.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler(
            filename=Path("logs/voicevox.log"),
            encoding="utf-8",
            maxBytes=32 * 1024 * 1024,
            backupCount=5,
        )

        dt_fmt = "%d-%m-%Y %H:%M:%S"
        formatter = logging.Formatter(
            fmt="[{asctime}] [{levelname:<8}] {name}: {message}",
            datefmt=dt_fmt,
            style="{",
        )

        handler.setFormatter(formatter)
        log.addHandler(handler)
        yield
    finally:
        handlers = log.handlers
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


async def logic(voicevox: Voicevox, wannaexit: bool) -> bool:
    """Core logic."""
    print("Here's what you can do:")
    print("0: Update speakers info + files")
    if voicevox.has_speakers_information:
        print("1: Choose a speaker")
    if voicevox.has_chosen_speaker:
        print("2: Generate necessary json")
    if voicevox.has_chosen_text and voicevox.has_chosen_speaker:
        print("3: Get generated audio file")
        print("4: Morphing from 2 speakers audio")
    print("5: Exit")

    selection: str = input("What would you like to do:")

    match selection:
        case "0":
            speaker = await voicevox.updatespeakers()

        case "1":
            speaker = await voicevox.select_speaker()
            if speaker:
                voicevox.speaker1, voicevox.style1 = speaker

        case "2":
            text: str = input("Japanese text:")
            await voicevox.jsonqueryget(text)

        case "3":
            await voicevox.simplesynthesis()

        case "4":
            speaker = await voicevox.select_speaker()
            if speaker:
                voicevox.speaker2, voicevox.style2 = speaker

                selectedmorphing = float(input("Set value from 0 to 1 (e.g 0.4):"))
                await voicevox.synthesismorphing(selectedmorphing)

        case "5":
            wannaexit = True
        case _:
            print("Not a proper option. Try again.")

    return wannaexit


async def main() -> None:
    """Run the script."""
    wannaexit = False

    async with ClientSession() as session:
        voicevox = Voicevox(session, URL)
        while wannaexit is False:
            wannaexit = await logic(voicevox, wannaexit)


if __name__ == "__main__":
    with setup_logging():
        uvloop.run(main())
