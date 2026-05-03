"""Speech synthesis and all that good stuff."""

import base64
import logging
from pathlib import Path
from typing import Literal, NotRequired, TypedDict, final

import orjson
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError, ServerDisconnectedError

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


class Mora(TypedDict, total=False):
    """JSON object."""

    text: str
    consonant: NotRequired[str]
    consonant_length: NotRequired[float]
    vowel: str
    vowel_length: float
    pitch: float


class AccentPhrase(TypedDict, total=False):
    """JSON object."""

    moras: list[Mora]
    accent: int
    pause_mora: NotRequired[Mora]
    is_interrogative: NotRequired[bool]


class AudioQuery(TypedDict, total=False):
    """JSON object."""

    accent_phrases: list[AccentPhrase]
    speedScale: float
    pitchScale: float
    intonationScale: float
    volumeScale: float
    prePhenomeLength: float
    postPhenomeLength: float
    pauseLength: NotRequired[float]
    pauseLengthScale: NotRequired[float]
    outputSamplingRate: int
    outputStereo: bool
    kana: NotRequired[str]


@final
class Voicevox:
    """Interface for Voicevox."""

    def __init__(self, session: ClientSession, url: str) -> None:
        """Initialize the session for http requests."""
        self.session = session
        self.url = url
        self.speakers: list[Speaker] = []
        self.audio_query: AudioQuery | None = None
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
        return Path("speakers.json").exists() or any(self.speakers)

    @property
    def has_chosen_text(self) -> bool:
        """Has the user made a query for the moras."""
        return Path("query.json").exists() or self.audio_query is not None

    @property
    def has_chosen_speaker(self) -> bool:
        """Has the user chosen speaker1."""
        return self.style1 is not None and self.speaker1 is not None

    async def select_speaker(
        self, use_saved: bool = False
    ) -> tuple[Speaker, Style] | None:
        """Select a style."""
        if not self.has_speakers_information:
            log.info("User hasn't queried the speaker information yet.")
            return

        if use_saved:
            with Path("speakers.json").open("r", encoding="utf-8") as j:
                speakers: list[Speaker] = orjson.loads(j.read())  # pyright: ignore[reportAny]
        else:
            speakers = self.speakers

        print("List of speakers:")
        for index, speaker in enumerate(speakers):
            print(f"{index}: {speaker['name']}")

        try:
            selectedspeaker: int = int(input("Which speaker would you like to select:"))
        except ValueError:
            print("You may only input a speaker id.")
            return
        if selectedspeaker + 1 > len(speakers) or selectedspeaker < 0:
            print("Not a proper speaker. Choose again.")
            return

        print("List of styles:")
        styles = speakers[selectedspeaker]["styles"]
        for i, style in enumerate(styles):
            print(f"{i}: Name: {style['name']} (id: {style['id']})")

        try:
            selectedstyle = int(input("Which style would you like to choose:"))
        except ValueError:
            print("You did not input a valid id.")
            return
        if selectedstyle + 1 > len(styles) or selectedstyle < 0:
            print("Not a proper style. Choose again.")
            return

        speaker = speakers[selectedspeaker]
        style = speakers[selectedspeaker]["styles"][selectedstyle]

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

    async def updatespeakers(self, save: bool = False) -> None:
        """Update speaker information."""
        try:
            async with self.session.get(f"{self.url}/speakers") as res:
                if res.status != OK and res.content_type != "application/json":
                    return
                data = await res.read()
            self.speakers = orjson.loads(data)
        except ClientConnectorError:
            log.warning("Voicevox is not available.")
            return

        if not save:
            return

        with open("speakers.json", "bw") as f:
            _ = f.write(data)

        speakeruuids: list[str] = [speaker["speaker_uuid"] for speaker in self.speakers]
        for speaker in speakeruuids:
            log.debug("Updating info for speaker %s", speaker)

            path = Path(f"speakers/{speaker}")
            if not path.exists():
                path.mkdir(parents=True)

            async with self.session.get(
                f"{self.url}/speaker_info", params={"speaker_uuid": speaker}
            ) as res:
                if res.status != OK or res.content_type != "application/json":
                    log.warning("Voicevox did not give speaker information.")
                    return
                speakerInfo: SpeakerInfo = orjson.loads(await res.read())  # pyright: ignore[reportAny]

            with path.joinpath("policy.md").open("wb") as f:
                _ = f.write(speakerInfo["policy"].encode())

            with path.joinpath("portrait.png").open("wb") as f:
                _ = f.write(base64.b64decode(speakerInfo["portrait"]))

            style_info = speakerInfo["style_infos"]
            for index, style in enumerate(style_info):
                style_id = speakerInfo["style_infos"][index]["id"]
                path = Path(f"speakers/{speaker}/styles/{style_id}")
                if not path.exists():
                    path.mkdir(parents=True)

                with path.joinpath(f"{style_id}.png").open("bw") as f:
                    _ = f.write(base64.b64decode(style["icon"]))

                samples = speakerInfo["style_infos"][index]["voice_samples"]
                for i, sample in enumerate(samples):
                    samplebinary = base64.b64decode(sample)

                    with path.joinpath(f"{i}.wav").open("bw") as f:
                        _ = f.write(samplebinary)

                    log.debug("Ended updating info for speaker %s", speaker)

    async def jsonqueryget(self, text: str, save: bool = False) -> None:
        """Turn text into json."""
        if self.style1 is None:
            log.info("The user didn't select a style yet.")
            return

        params = {"speaker": self.style1["id"], "text": text}
        async with self.session.post(
            f"{self.url}/audio_query", params=params, headers=JSON_HEADERS
        ) as res:
            if res.status == OK and res.content_type == "application/json":
                data = await res.read()
                if save:
                    with open("query.json", "bw") as f:
                        _ = f.write(await res.read())
                self.audio_query = orjson.loads(data)

    async def simplesynthesis(self, use_saved: bool = False) -> None:
        """Synthesize speech."""
        if self.style1 is None or not self.has_chosen_text:
            log.info("The user didn't select a style or didn't make a query yet.")
            return

        if use_saved:
            with open("query.json") as f:
                audio_query = f.read().encode("utf-8")
        audio_query = orjson.dumps(self.audio_query)
        try:
            async with self.session.post(
                f"{self.url}/synthesis",
                params={"speaker": self.style1["id"]},
                data=audio_query,
                headers=JSON_HEADERS,
            ) as res:
                if res.status == OK and res.content_type == "audio/wav":
                    with open("audio.wav", mode="bw") as f:
                        _ = f.write(await res.read())
        except ServerDisconnectedError as e:
            print("The server disconnected")
            log.exception("The server disconnected", exc_info=e)

    async def can_morph(self) -> bool:
        """Check if 2 speakers can morph."""
        if self.speaker1 is None or self.speaker2 is None:
            return False
        allowed_morphing = self.speaker1["supported_features"]
        if allowed_morphing["permitted_synthesis_morphing"] == "NOTHING":
            return False
        elif allowed_morphing["permitted_synthesis_morphing"] == "ALL":
            return True
        elif allowed_morphing["permitted_synthesis_morphing"] == "SELF_ONLY":
            if self.speaker1["speaker_uuid"] == self.speaker2["speaker_uuid"]:
                return True
            else:
                return False
        else:  # Either the speaker is missing some data, or its corrupted.
            return False

    async def synthesismorphing(
        self, morphrate: float, use_saved: bool = False
    ) -> None:
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
            "base_speaker": self.style1["id"],
            "target_speaker": self.style2["id"],
            "morph_rate": morphrate,
        }
        if use_saved:
            with open("query.json") as f:
                audio_query = f.read().encode("utf-8")
        audio_query = orjson.dumps(self.audio_query)

        async with self.session.post(
            f"{self.url}/synthesis_morphing",
            params=params,
            data=audio_query,
            headers=JSON_HEADERS,
        ) as res:
            if res.status == OK and res.content_type == "audio/wav":
                with open("audio.wav", mode="bw") as f:
                    _ = f.write(await res.read())
