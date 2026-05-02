"""Speech synthesis and all that good stuff."""

import base64
import logging
from pathlib import Path
from typing import Literal, TypedDict, final

import orjson
from aiohttp import ClientSession

log = logging.getLogger(__name__)

OK = 200
JSON_HEADERS = {"Content-Type": "application/json"}


class Style(TypedDict):
    """JSON object."""

    name: str
    id: int
    type: str


class StyleInfo(TypedDict):
    """JSON object."""

    id: int
    icon: str
    portrait: str
    voice_samples: list[str]


class SupportedFeatures(TypedDict):
    """JSON object."""

    permitted_synthesis_morphing: Literal["ALL", "SELF_ONLY", "NOTHING"]
    """Who the character can morph with."""


class Speaker(TypedDict):
    """JSON object."""

    name: str
    """The speaker's name"""
    speaker_uuid: str
    """The speaker's uuid"""
    styles: list[Style]
    """The speaker's styles"""
    version: str
    """The speaker's version"""
    supported_features: SupportedFeatures
    """The speaker's supported features."""


class SpeakerInfo(TypedDict):
    """JSON object."""

    policy: str
    portrait: str
    style_infos: list[StyleInfo]


@final
class Voicevox:
    """Interface for Voicevox."""

    def __init__(self, session: ClientSession, url: str) -> None:
        """Initialize the session for http requests."""
        self.session = session
        self.url = url
        self.speaker1: Speaker | None = None
        """Currently chosen speaker 1."""
        self.style1: Style | None = None
        """Currently chosen style for speaker 1."""
        self.speaker2: Speaker | None = None
        """Currently chosen speaker 2."""
        self.style2: Style | None = None
        """Currently chosen style for speaker 2."""

    @property
    def has_speakers_information(self) -> bool:
        """Has the user initialized the speaker information."""
        return Path("speakers.json").exists()

    @property
    def has_chosen_text(self) -> bool:
        """Has the user made a query for the moras."""
        return Path("query.json").exists()

    @property
    def has_chosen_speaker(self) -> bool:
        """Has the user chosen speaker1."""
        return self.style1 is not None and self.speaker1 is not None

    async def select_speaker(self) -> tuple[Speaker, Style] | None:
        """Select a style."""
        if not self.has_speakers_information:
            log.info("User hasn't queried the speaker information yet.")
            return

        with Path("speakers.json").open("r", encoding="utf-8") as j:
            data: list[Speaker] = orjson.loads(j.read())  # pyright: ignore[reportAny]
        speakerlist: list[str] = [item["name"] for item in data]

        print("List of speakers:")
        index: int = -1
        minimumindex = 0
        for _ in speakerlist:
            index = index + 1
            print(f"{index}:", speakerlist[index])

        try:
            selectedspeaker: int = int(input("Which speaker would you like to select:"))
        except ValueError:
            print("You may only input the speaker id.")
            return
        if selectedspeaker > index or selectedspeaker < minimumindex:
            print("Not a proper speaker. Choose again.")
            return

        else:
            stylelist = data[selectedspeaker]["styles"]
            styleindex = -1
            print("List of styles:")
            for _ in stylelist:
                styleindex = styleindex + 1
                selectableid = stylelist[styleindex]["id"]
                selectablename = stylelist[styleindex]["name"]
                print(f"{styleindex}:", "Name:", selectablename, "id:", selectableid)

            try:
                selectedstyle = int(input("Which style would you like to choose:"))
            except ValueError:
                print("You did not input a valid id.")
                return
            if selectedstyle > styleindex or selectedstyle < minimumindex:
                print("Not a proper style. Choose again.")
                return

            speaker = data[selectedspeaker]
            style = data[selectedspeaker]["styles"][selectedstyle]

            print(
                "You have choosen",
                speaker["name"],
                speaker["speaker_uuid"],
                "with the style",
                style["name"],
                "id:",
                style["id"],
            )
            log.info("User selected style %s", style["id"])

        return speaker, style

    async def updatespeakers(self) -> None:
        """Update speaker information."""
        async with self.session.get(f"{self.url}/speakers") as res:
            if res.status == OK and res.content_type == "application/json":
                with open("speakers.json", "bw") as f:
                    _ = f.write(await res.read())

        with Path("speakers.json").open("r", encoding="utf-8") as j:
            data: list[Speaker] = orjson.loads(j.read())  # pyright: ignore[reportAny]
        speakeruuid: list[str] = [item["speaker_uuid"] for item in data]

        for speaker in speakeruuid:
            log.debug("Updating info for speaker %s", speaker)
            params: dict[str, str] = {"speaker_uuid": speaker}

            async with self.session.get(
                f"{self.url}/speaker_info", params=params
            ) as res:
                if res.status == OK and res.content_type == "application/json":
                    path = Path(f"speakers/{speaker}")
                    if not path.exists():
                        path.mkdir(parents=True)

                    with path.joinpath(f"{speaker}.json").open("bw") as f:
                        _ = f.write(await res.read())

                    with path.joinpath(f"{speaker}.json").open("r") as j:
                        decodedj: SpeakerInfo = orjson.loads(j.read())  # pyright: ignore[reportAny]

                    image_binary = base64.b64decode(decodedj["portrait"])
                    with path.joinpath(f"{speaker}.png").open("wb") as f:
                        _ = f.write(image_binary)

                    styleids = decodedj["style_infos"]

                    for index, style in enumerate(styleids):
                        icon_binary = base64.b64decode(style["icon"])
                        styleindex = decodedj["style_infos"][index]["id"]
                        path = Path(f"speakers/{speaker}/styles/{styleindex}")

                        if not path.exists():
                            path.mkdir(parents=True)

                        with path.joinpath(f"{styleindex}.png").open("bw") as f:
                            _ = f.write(icon_binary)

                        samples = decodedj["style_infos"][index]["voice_samples"]
                        sampleindex = -1
                        for _ in samples:
                            sampleindex = sampleindex + 1
                            samplebinary = base64.b64decode(samples[sampleindex])

                            with path.joinpath(f"{sampleindex}.wav").open("bw") as f:
                                _ = f.write(samplebinary)

                    log.debug("Ended updating info for speaker %s", speaker)

    async def jsonqueryget(self, text: str) -> None:
        """Turn text into json."""
        if self.style1 is None:
            log.info("The user didn't select a style yet.")
            return

        params = {
            "speaker": self.style1.get("id"),
            "text": text,
        }
        async with self.session.post(f"{self.url}/audio_query", params=params) as res:
            if res.status == OK and res.content_type == "application/json":
                with open("query.json", "bw") as f:
                    _ = f.write(await res.read())

    async def simplesynthesis(self) -> None:
        """Synthesize speech."""
        if self.style1 is None or not self.has_chosen_text:
            log.info("The user didn't select a style or didn't make a query yet.")
            return

        params: dict[str, int] = {"speaker": self.style1.get("id")}

        with open("query.json") as f:
            data = f.read().encode("utf-8")

        async with self.session.post(
            f"{self.url}/synthesis", params=params, data=data, headers=JSON_HEADERS
        ) as res:
            if res.status == OK and res.content_type == "audio/wav":
                with open("audio.wav", mode="bw") as f:
                    _ = f.write(await res.read())

    async def can_morph(self) -> bool:
        """Check if 2 speakers can morph."""
        if self.speaker1 is None or self.speaker2 is None:
            return False
        allowed_morphing = self.speaker1.get("supported_features")
        if allowed_morphing["permitted_synthesis_morphing"] == "NOTHING":
            return False
        elif allowed_morphing["permitted_synthesis_morphing"] == "ALL":
            return True
        elif allowed_morphing["permitted_synthesis_morphing"] == "SELF_ONLY":
            if self.speaker2.get("styles") == self.speaker1.get("styles"):
                return True
            else:
                return False
        else:  # Either the speaker is missing some data, or its corrupted.
            return False

    async def synthesismorphing(self, morphrate: float) -> None:
        """Morph speech between 2 speakers."""
        if (
            not self.style1
            or not self.style2
            or not self.has_chosen_text
            or not self.speaker1
            or not self.speaker2
        ):
            return

        if not await self.can_morph():
            log.info(
                "Can not morph speaker %s with speaker %s since their features were %s",
                self.speaker1["name"],
                self.speaker2["name"],
                self.speaker1["supported_features"],
            )
            return

        params = {
            "base_speaker": self.style1.get("id"),
            "target_speaker": self.style2.get("id"),
            "morph_rate": morphrate,
        }

        with open("query.json") as f:
            data = f.read().encode("utf-8")

        async with self.session.post(
            f"{self.url}/synthesis_morphing",
            params=params,
            data=data,
            headers=JSON_HEADERS,
        ) as res:
            if res.status == OK and res.content_type == "audio/wav":
                with open("audio.wav", mode="bw") as f:
                    _ = f.write(await res.read())
