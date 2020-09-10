from typing import Dict, List
import utils
from data import Playlist, Track
from copy import deepcopy
import itertools
import re


def get_playlist_name_without_prefix(tags: Dict[str, str]) -> str:
    """
    Example: { "genre": "Acid", "rating": "4" } => "ge=Acid ra=4"
    """
    name = ""
    for k in sorted(tags.keys()):
        name += "%s%s=%s " % (k[0], k[1], tags[k].replace(" ", "_"))
    return name.strip()


def get_playlist_prefix(tag_keys: List[str], index: int) -> str:
    """
    Example: (["rating", "genre"], 2) => "02_RaGe"
    """
    tags_initials = "".join(["%s%s" % (k[0].upper(), k[1]) for k in tag_keys])
    return "%02d_%s " % (index, tags_initials)


def get_playlist_name_from_tags(tags: Dict[str, str], index: int):
    return "%s%s" % (get_playlist_prefix(tags.keys(), index), get_playlist_name_without_prefix(tags))


def trim_playlist_prefix(playlist_name: str) -> str:
    """
    Example: "02_RaGe ge=Acid ra=4" => "ge=Acid ra=4"
    """
    return playlist_name.split(" ", 1)[1]


def tags_from_playlist_name(playlist_name: str, tag_models: Dict[str, List[str]]):
    name_without_prefix = trim_playlist_prefix(playlist_name)
    matches = re.findall(r'([a-zA-Z0-9_-]+)=([a-zA-Z0-9_-]+)', name_without_prefix)
    tags = dict()
    for match in matches:
        identified_tag_key = utils.identify_value_from_prefix(match[0], list(tag_models.keys()))
        if identified_tag_key:
            tag_value = match[1].replace("_", " ")
            if tag_value in tag_models[identified_tag_key]:
                tags[identified_tag_key] = tag_value
    return tags


class AutoGeneratedPlaylistManager:

    def __init__(self, tag_models: Dict[str, List[str]], playlists_to_generate: List[List[str]]):
        self._tag_models = tag_models
        self._playlists_to_generate = playlists_to_generate

    def tagged_tracks_from_playlists(self, playlists: List[Playlist]) -> Dict[str, Track]:
        tracks = dict()
        for p in playlists:
            playlist_tags = tags_from_playlist_name(p.name, self._tag_models)
            for t in p.tracks:
                if str(t.path) not in tracks:
                    tracks[str(t.path)] = deepcopy(t)
                playlist_tags.pop("rating", None)
                tracks[str(t.path)].tags.update(playlist_tags)

        return tracks

    def playlists_from_tagged_tracks(self, tracks: Dict[str, Track]) -> List[Playlist]:
        playlists = []
        for playlist_prefix_index, tag_keys_to_generate_playlist in enumerate(self._playlists_to_generate):
            for tag_values in itertools.product(
                    *[self._tag_models[tag_key] for tag_key in tag_keys_to_generate_playlist]):
                playlist_tags = {tag_keys_to_generate_playlist[i]: tag_values[i] for i, _ in enumerate(tag_values)}
                track_list = []
                for t in tracks.values():
                    if t.tags.items() >= playlist_tags.items():
                        track_list.append(t)
                if not track_list:
                    continue
                playlists.append(Playlist(
                    get_playlist_name_from_tags(playlist_tags, playlist_prefix_index),
                    track_list
                ))
        return playlists


if __name__ == "__main__":
    assert get_playlist_name_without_prefix({ "genre": "Acid", "rating": "4" }) == "ge=Acid ra=4"
    assert get_playlist_name_without_prefix({ "rating": "4", "genre": "Acid" }) == "ge=Acid ra=4"
    assert get_playlist_name_without_prefix({ "rating": "4", "genre": "Deep House" }) == "ge=Deep_House ra=4"
    assert get_playlist_prefix(["rating", "genre"], 2) == "02_RaGe "
    assert get_playlist_prefix(["genre", "rating"], 10) == "10_GeRa "
    assert trim_playlist_prefix("02_RaGe ge=Acid ra=4") == "ge=Acid ra=4"

    from constants import *
    import json

    with open(SCANNER_TAGS_FILE) as json_file:
        TAGS_MODEL = json.load(json_file)

    assert json.dumps(tags_from_playlist_name("02_RaGe ge=Acid ra=4", TAGS_MODEL)) == json.dumps({'genre2': 'Acid', 'rating': '4'})
    assert json.dumps(tags_from_playlist_name("02_RaGe ge=Deep_House ra=4", TAGS_MODEL)) == json.dumps({'genre2': 'Deep House', 'rating': '4'})
