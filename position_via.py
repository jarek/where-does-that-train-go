import math
from pprint import pprint

import requests


URL = 'https://tsimobile.viarail.ca/data/allData.json'


def train_with_distance(train, loc):
    train['distance'] = math.sqrt(math.pow((train['position'][0] - loc[0]), 2) +
                                  math.pow((train['position'][1] - loc[1]), 2))

    return train


def parse_train(train, train_id):
    stations = [t['station'] for t in train['times']]

    return {
        'trip_number': train_id,
        'position': (train['lat'], train['lng']),
        'moving': train['speed'] > 0,
        'direction': train['direction'],
        'to': stations[-1],
        'via': stations[:-1]
    }


def parse_trains():
    r = requests.get(URL)
    all_trains = r.json()

    departed_trains = {train_id: train for train_id, train in all_trains.items()
                       if train['departed']}

    pprint(departed_trains)

    trains_with_numbers = [
        parse_train(train, train_id)
        for train_id, train in departed_trains.items()
    ]

    # VIA sometimes reports trains that are lost:
    #   "lat":null,"lng":null,"speed":0,"direction":null,"departed":true
    trains_with_positions = [
        train for train in trains_with_numbers
        if train['position'][0] != None
    ]

    return trains_with_positions


if __name__ == '__main__':
    trains = parse_trains()

    loc = (43.641, -79.417)

    trains_with_distance = [
        train_with_distance(train, loc)
        for train in trains
    ]

    sorted_trains = sorted(trains, key=lambda t: t['distance'])

    pprint(sorted_trains[:5])
