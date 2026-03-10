from __future__ import annotations

import argparse
import json
import warnings
from dataclasses import asdict, dataclass
from typing import Iterable

from soco.discovery import discover


@dataclass(slots=True)
class SpeakerSummary:
    name: str
    ip: str
    coordinator: bool
    visible: bool
    model: str | None = None
    group: str | None = None


def discover_speakers(timeout: int = 5) -> list:
    speakers = discover(timeout=timeout)
    if not speakers:
        return []
    return sorted(speakers, key=lambda speaker: speaker.player_name.casefold())


def summarize_speaker(speaker) -> SpeakerSummary:
    model = None
    group_name = None

    try:
        model = speaker.get_speaker_info().get("model_name")
    except Exception:
        model = None

    try:
        group_name = speaker.group.coordinator.player_name
    except Exception:
        group_name = None

    return SpeakerSummary(
        name=speaker.player_name,
        ip=speaker.ip_address,
        coordinator=bool(speaker.is_coordinator),
        visible=bool(speaker.is_visible),
        model=model,
        group=group_name,
    )


def resolve_speaker(room: str, speakers: Iterable):
    room_key = room.casefold()
    speakers = list(speakers)

    exact = [
        speaker
        for speaker in speakers
        if speaker.player_name.casefold() == room_key or speaker.ip_address == room
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise SystemExit(f"More than one speaker matched '{room}'. Use the IP address instead.")

    partial = [
        speaker
        for speaker in speakers
        if room_key in speaker.player_name.casefold() or room_key in speaker.ip_address.casefold()
    ]
    if len(partial) == 1:
        return partial[0]
    if not partial:
        raise SystemExit(f"No Sonos speaker matched '{room}'.")

    names = ", ".join(f"{speaker.player_name} ({speaker.ip_address})" for speaker in partial)
    raise SystemExit(f"Room '{room}' is ambiguous. Matches: {names}")


def get_favorites(speaker) -> list[dict]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = speaker.get_sonos_favorites()
    return list(result.get("favorites", []))


def resolve_favorite(name: str, favorites: list[dict]) -> dict:
    key = name.casefold()

    exact = [favorite for favorite in favorites if favorite.get("title", "").casefold() == key]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise SystemExit(f"More than one favorite matched '{name}'.")

    partial = [favorite for favorite in favorites if key in favorite.get("title", "").casefold()]
    if len(partial) == 1:
        return partial[0]
    if not partial:
        raise SystemExit(f"No Sonos favorite matched '{name}'.")

    titles = ", ".join(favorite.get("title", "<untitled>") for favorite in partial)
    raise SystemExit(f"Favorite '{name}' is ambiguous. Matches: {titles}")


def print_speakers(speakers: list, as_json: bool = False) -> None:
    summaries = [summarize_speaker(speaker) for speaker in speakers]
    if as_json:
        print(json.dumps([asdict(summary) for summary in summaries], indent=2))
        return

    if not summaries:
        print("No Sonos speakers found.")
        return

    for summary in summaries:
        coordinator = "coordinator" if summary.coordinator else "member"
        visible = "visible" if summary.visible else "hidden"
        extras = [coordinator, visible]
        if summary.model:
            extras.append(summary.model)
        if summary.group:
            extras.append(f"group={summary.group}")
        print(f"- {summary.name} ({summary.ip}) [{', '.join(extras)}]")


def command_discover(args: argparse.Namespace) -> int:
    speakers = discover_speakers(timeout=args.timeout)
    print_speakers(speakers, as_json=args.json)
    return 0 if speakers else 1


def command_favorites(args: argparse.Namespace) -> int:
    speakers = discover_speakers(timeout=args.timeout)
    if not speakers:
        raise SystemExit("No Sonos speakers found.")

    speaker = resolve_speaker(args.room, speakers) if args.room else speakers[0]
    favorites = get_favorites(speaker)

    if args.json:
        print(json.dumps(favorites, indent=2))
        return 0

    if not favorites:
        print(f"No Sonos favorites found on {speaker.player_name}.")
        return 0

    print(f"Favorites from {speaker.player_name}:")
    for favorite in favorites:
        print(f"- {favorite.get('title', '<untitled>')}: {favorite.get('uri', '')}")
    return 0


def command_play_favorite(args: argparse.Namespace) -> int:
    speakers = discover_speakers(timeout=args.timeout)
    if not speakers:
        raise SystemExit("No Sonos speakers found.")

    speaker = resolve_speaker(args.room, speakers)
    favorites = get_favorites(speaker)
    favorite = resolve_favorite(args.favorite, favorites)

    speaker.play_uri(
        uri=favorite.get("uri", ""),
        meta=favorite.get("meta", ""),
        title=favorite.get("title", ""),
        force_radio=args.force_radio,
    )
    print(f"Playing '{favorite.get('title', '<untitled>')}' on {speaker.player_name}.")
    return 0


def command_play_uri(args: argparse.Namespace) -> int:
    speakers = discover_speakers(timeout=args.timeout)
    if not speakers:
        raise SystemExit("No Sonos speakers found.")

    speaker = resolve_speaker(args.room, speakers)
    speaker.play_uri(
        uri=args.uri,
        meta=args.meta,
        title=args.title,
        force_radio=args.force_radio,
    )
    print(f"Playing URI on {speaker.player_name}: {args.uri}")
    return 0


def command_pause(args: argparse.Namespace) -> int:
    speakers = discover_speakers(timeout=args.timeout)
    if not speakers:
        raise SystemExit("No Sonos speakers found.")

    speaker = resolve_speaker(args.room, speakers)
    speaker.pause()
    print(f"Paused {speaker.player_name}.")
    return 0


def command_resume(args: argparse.Namespace) -> int:
    speakers = discover_speakers(timeout=args.timeout)
    if not speakers:
        raise SystemExit("No Sonos speakers found.")

    speaker = resolve_speaker(args.room, speakers)
    speaker.play()
    print(f"Resumed {speaker.player_name}.")
    return 0


def command_volume(args: argparse.Namespace) -> int:
    speakers = discover_speakers(timeout=args.timeout)
    if not speakers:
        raise SystemExit("No Sonos speakers found.")

    speaker = resolve_speaker(args.room, speakers)
    if not 0 <= args.level <= 100:
        raise SystemExit("Volume must be between 0 and 100.")

    speaker.volume = args.level
    print(f"Set {speaker.player_name} volume to {args.level}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sonos-remote",
        description="Discover Sonos speakers on your local network and control basic playback.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover", help="Scan your network for Sonos speakers.")
    discover_parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout in seconds.")
    discover_parser.add_argument("--json", action="store_true", help="Print discovered speakers as JSON.")
    discover_parser.set_defaults(func=command_discover)

    scan_parser = subparsers.add_parser("scan", help="Alias for discover.")
    scan_parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout in seconds.")
    scan_parser.add_argument("--json", action="store_true", help="Print discovered speakers as JSON.")
    scan_parser.set_defaults(func=command_discover)

    favorites_parser = subparsers.add_parser("favorites", help="List Sonos favorites.")
    favorites_parser.add_argument("room", nargs="?", help="Room name or speaker IP. Defaults to the first discovered speaker.")
    favorites_parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout in seconds.")
    favorites_parser.add_argument("--json", action="store_true", help="Print favorites as JSON.")
    favorites_parser.set_defaults(func=command_favorites)

    play_favorite_parser = subparsers.add_parser("play-favorite", help="Play a Sonos favorite by title.")
    play_favorite_parser.add_argument("room", help="Room name or speaker IP.")
    play_favorite_parser.add_argument("favorite", help="Favorite title. Partial matches are allowed when unique.")
    play_favorite_parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout in seconds.")
    play_favorite_parser.add_argument("--force-radio", action="store_true", help="Treat the URI as a radio stream.")
    play_favorite_parser.set_defaults(func=command_play_favorite)

    play_uri_parser = subparsers.add_parser("play-uri", help="Play a URI directly on a speaker.")
    play_uri_parser.add_argument("room", help="Room name or speaker IP.")
    play_uri_parser.add_argument("uri", help="URI to play.")
    play_uri_parser.add_argument("--title", default="", help="Optional display title.")
    play_uri_parser.add_argument("--meta", default="", help="Optional DIDL-Lite metadata.")
    play_uri_parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout in seconds.")
    play_uri_parser.add_argument("--force-radio", action="store_true", help="Treat the URI as a radio stream.")
    play_uri_parser.set_defaults(func=command_play_uri)

    pause_parser = subparsers.add_parser("pause", help="Pause playback in a room.")
    pause_parser.add_argument("room", help="Room name or speaker IP.")
    pause_parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout in seconds.")
    pause_parser.set_defaults(func=command_pause)

    resume_parser = subparsers.add_parser("resume", help="Resume playback in a room.")
    resume_parser.add_argument("room", help="Room name or speaker IP.")
    resume_parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout in seconds.")
    resume_parser.set_defaults(func=command_resume)

    volume_parser = subparsers.add_parser("volume", help="Set room volume.")
    volume_parser.add_argument("room", help="Room name or speaker IP.")
    volume_parser.add_argument("level", type=int, help="Volume between 0 and 100.")
    volume_parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout in seconds.")
    volume_parser.set_defaults(func=command_volume)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))
