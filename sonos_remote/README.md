# sonos-remote

A small CLI for discovering Sonos speakers on your local network and controlling basic playback.

## Setup

From the workspace root:

```bash
uv sync
```

## Discover speakers

```bash
uv run --package sonos-remote sonos-remote discover
```

or:

```bash
uv run --package sonos-remote sonos-remote scan --json
```

## List Sonos favorites

```bash
uv run --package sonos-remote sonos-remote favorites
uv run --package sonos-remote sonos-remote favorites "Living Room"
```

## Play a Sonos favorite

```bash
uv run --package sonos-remote sonos-remote play-favorite "Living Room" "Jazz Vibes"
```

## Play a URI directly

```bash
uv run --package sonos-remote sonos-remote play-uri "Living Room" "https://example.com/stream.mp3" --title "Example Stream" --force-radio
```

## Pause / resume / volume

```bash
uv run --package sonos-remote sonos-remote pause "Living Room"
uv run --package sonos-remote sonos-remote resume "Living Room"
uv run --package sonos-remote sonos-remote volume "Living Room" 25
```

## Notes

- Discovery works only when this command is run on the same local network as your Sonos system.
- `play-favorite` uses Sonos favorites already configured in your Sonos app.
- Streaming arbitrary services like Spotify usually works best through a saved Sonos favorite or service-native integration.
