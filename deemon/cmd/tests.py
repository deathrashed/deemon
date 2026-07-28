import logging
import re

from deezer import Deezer

from deemon.core.config import Config as config

logger = logging.getLogger(__name__)
dz = Deezer()


def exclusion_test(url):
    match = False

    try:
        album_id = int(url.split('/album/')[1].split('?')[0])
    except (IndexError, ValueError):
        logger.info(f"Invalid url: {url}")
        return

    album = dz.api.get_album(album_id)
    print(f"Artist: {album['artist']['name']}")
    print(f"Album: {album['title']}\n")

    if config.exclusion_patterns():
        print("Checking for the following patterns:")
        for index, pattern in enumerate(config.exclusion_patterns(), start=1):
            matched = bool(re.search(pattern, album['title'].lower()))
            print(f"  {index}.  {pattern}   >>   {'** MATCH **' if matched else 'NO MATCH'}")
            match = match or matched

    if config.exclusion_keywords():
        print("\nChecking for the following keywords:")
        title_groups = re.search(r'\(([^)]+)\)|\[([^]]+)]', album['title'].lower())
        title_suffix = title_groups.group() if title_groups else ''
        for index, keyword in enumerate(config.exclusion_keywords(), start=1):
            matched = keyword in title_suffix
            print(f"  {index}.  {keyword}   >>   {'** MATCH **' if matched else 'NO MATCH'}")
            match = match or matched

    print("\nResult: This release would be excluded" if match else "\nResult: This release would NOT be excluded")
