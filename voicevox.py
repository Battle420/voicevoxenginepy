"""Speech synthesis and all that good stuff."""

import base64
import logging
from pathlib import Path
from typing import Literal, final

import msgspec
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError, ServerDisconnectedError

log = logging.getLogger(__name__)

OK = 200
JSON_HEADERS = {"Content-Type": "application/json"}


class SpeakerStyle(msgspec.Struct):
    """JSON object."""

    name: str
    id: int
    type: Literal["talk", "singing_teacher", "frame_decode", "sing"]


class StyleInfo(msgspec.Struct):
    """JSON object."""

    id: int
    icon: str
    portrait: str | None
    voice_samples: list[str]


class SupportedFeatures(msgspec.Struct):
    """JSON object."""

    permitted_synthesis_morphing: Literal["ALL", "SELF_ONLY", "NOTHING"]
    """Who the character can morph with."""


class Speaker(msgspec.Struct):
    """JSON object."""

    name: str
    """The speaker's name"""
    speaker_uuid: str
    """The speaker's uuid"""
    styles: list[SpeakerStyle]
    """The speaker's styles"""
    version: str
    """The speaker's version"""
    supported_features: SupportedFeatures
    """The speaker's supported features."""


class SpeakerInfo(msgspec.Struct):
    """JSON object."""

    policy: str
    portrait: str
    style_infos: list[StyleInfo]


class Mora(msgspec.Struct):
    """JSON object."""

    text: str
    consonant: str | None
    consonant_length: float | None
    vowel: str
    vowel_length: float
    pitch: float


class AccentPhrase(msgspec.Struct):
    """JSON object."""

    moras: list[Mora]
    accent: int
    pause_mora: Mora | None
    is_interrogative: bool | None


class AudioQuery(msgspec.Struct):
    """JSON object."""

    accent_phrases: list[AccentPhrase]
    speedScale: float
    pitchScale: float
    intonationScale: float
    volumeScale: float
    prePhonemeLength: float
    postPhonemeLength: float
    pauseLength: float | None
    pauseLengthScale: float | None
    outputSamplingRate: int
    outputStereo: bool
    kana: str | None


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
        self.style1: SpeakerStyle | None = None
        """Currently chosen style for speaker 1."""
        self.speaker2: Speaker | None = None
        """Currently chosen speaker 2."""
        self.style2: SpeakerStyle | None = None
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
    ) -> tuple[Speaker, SpeakerStyle] | None:
        """Select a style."""
        if not self.has_speakers_information:
            log.info("User hasn't queried the speaker information yet.")
            return

        if use_saved:
            with Path("speakers.json").open("r", encoding="utf-8") as j:
                speakers = msgspec.json.decode(j.read(), type=list[Speaker])
        else:
            speakers = self.speakers

        print("List of speakers:")
        for index, speaker in enumerate(speakers):
            print(f"{index}: {speaker.name}")

        try:
            selectedspeaker: int = int(input("Which speaker would you like to select:"))
        except ValueError:
            print("You may only input a speaker id.")
            return
        if selectedspeaker + 1 > len(speakers) or selectedspeaker < 0:
            print("Not a proper speaker. Choose again.")
            return

        print("List of styles:")
        styles = speakers[selectedspeaker].styles
        forbidden_styles: list[int] = []
        for i, style in enumerate(styles):
            if style.type == "talk":
                print(f"{i}: Name: {style.name} (id: {style.id})")
            else:
                forbidden_styles.append(i)
                print(f"<!> Not a talk style {i} Name: {style.name} (id: {style.id})")

        try:
            selectedstyle = int(input("Which style would you like to choose:"))
        except ValueError:
            print("You did not input a valid id.")
            return
        if selectedstyle + 1 > len(styles) or selectedstyle < 0:
            print("Not a proper style. Choose again.")
            return
        elif selectedstyle in forbidden_styles:
            print("You may only select talking styles.")
            return

        speaker = speakers[selectedspeaker]
        style = speakers[selectedspeaker].styles[selectedstyle]

        print(
            "You have choosen",
            speaker.name,
            speaker.speaker_uuid,
            "with the style",
            style.name,
            "id:",
            style.id,
        )
        log.info("User selected style %s", style.id)

        return speaker, style

    async def updatespeakers(self, save: bool = False) -> None:
        """Update speaker information."""
        try:
            async with self.session.get(f"{self.url}/speakers") as res:
                if res.status != OK and res.content_type != "application/json":
                    return
                data = await res.read()
            self.speakers = msgspec.json.decode(data, type=list[Speaker])
        except ClientConnectorError:
            log.warning("Voicevox is not available.")
            return

        if not save:
            return

        with open("speakers.json", "bw") as f:
            _ = f.write(data)

        decoder = msgspec.json.Decoder(SpeakerInfo)
        speakeruuids: list[str] = [speaker.speaker_uuid for speaker in self.speakers]
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
                speakerInfo = decoder.decode(await res.read())

            with path.joinpath("policy.md").open("wb") as f:
                _ = f.write(speakerInfo.policy.encode())

            with path.joinpath("portrait.png").open("wb") as f:
                _ = f.write(base64.b64decode(speakerInfo.portrait))

            style_info = speakerInfo.style_infos
            for index, style in enumerate(style_info):
                style_id = speakerInfo.style_infos[index].id
                path = Path(f"speakers/{speaker}/styles/{style_id}")
                if not path.exists():
                    path.mkdir(parents=True)

                with path.joinpath(f"{style_id}.png").open("bw") as f:
                    _ = f.write(base64.b64decode(style.icon))

                if style.portrait:
                    with path.joinpath("portrait.png").open("bw") as f:
                        _ = f.write(base64.b64decode(style.portrait))

                samples = speakerInfo.style_infos[index].voice_samples
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

        params = {"speaker": self.style1.id, "text": text}
        async with self.session.post(
            f"{self.url}/audio_query", params=params, headers=JSON_HEADERS
        ) as res:
            if res.status != OK or res.content_type != "application/json":
                log.warning("Voicevox did not provide an audio query.")
                return
            data = await res.read()
        if save:
            with open("query.json", "bw") as f:
                _ = f.write(data)
        self.audio_query = msgspec.json.decode(data, type=AudioQuery)

    async def simplesynthesis(self, use_saved: bool = False) -> None:
        """Synthesize speech."""
        if self.style1 is None or not self.has_chosen_text:
            log.info("The user didn't select a style or didn't make a query yet.")
            return

        if use_saved:
            with open("query.json") as f:
                audio_query = f.read().encode("utf-8")
        else:
            audio_query = msgspec.json.encode(self.audio_query)
        try:
            async with self.session.post(
                f"{self.url}/synthesis",
                params={"speaker": self.style1.id},
                data=audio_query,
                headers=JSON_HEADERS,
            ) as res:
                if res.status != OK or res.content_type != "audio/wav":
                    log.warning("Voicevox did not provide audio.")
                    return
                with open("audio.wav", mode="bw") as f:
                    _ = f.write(await res.read())
        except ServerDisconnectedError as e:
            print("The server disconnected")
            log.exception("The server disconnected", exc_info=e)

    async def can_morph(self) -> bool:
        """Check if 2 speakers can morph."""
        if self.speaker1 is None or self.speaker2 is None:
            return False
        allowed_morphing = self.speaker1.supported_features
        if allowed_morphing.permitted_synthesis_morphing == "NOTHING":
            return False
        elif allowed_morphing.permitted_synthesis_morphing == "ALL":
            return True
        elif allowed_morphing.permitted_synthesis_morphing == "SELF_ONLY":
            if self.speaker1.speaker_uuid == self.speaker2.speaker_uuid:
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
            log.warning(
                "Can not morph speaker %s with speaker %s since their features were %s",
                self.speaker1.name,
                self.speaker2.name,
                self.speaker1.supported_features.permitted_synthesis_morphing,
            )
            return

        params = {
            "base_speaker": self.style1.id,
            "target_speaker": self.style2.id,
            "morph_rate": morphrate,
        }
        if use_saved:
            with open("query.json") as f:
                audio_query = f.read().encode("utf-8")
        else:
            audio_query = msgspec.json.encode(self.audio_query)

        async with self.session.post(
            f"{self.url}/synthesis_morphing",
            params=params,
            data=audio_query,
            headers=JSON_HEADERS,
        ) as res:
            if res.status == OK and res.content_type == "audio/wav":
                with open("audio.wav", mode="bw") as f:
                    _ = f.write(await res.read())
