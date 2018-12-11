import math
from pprint import pprint
from xml.etree import ElementTree as ET

import requests


URL = 'http://gotracker.ca/GoTracker/web/GODataAPIProxy.svc/TripLocation/Service/Lang/{line}/en'

LINES = {
    '65': {
        'corridor': 'Barrie',
        'directions_via': {
            'Allandale Waterfront GO': ['Downsview Park', 'Aurora', 'Newmarket'],
            'Bradford GO': ['Downsview Park', 'Aurora', 'Newmarket'],
            'Aurora GO': ['Downsview Park']
        }
    },
    '01': {
        'corridor': 'Lakeshore West',
        'directions_via': {
            'Hamilton GO Centre': ['Port Credit', 'Oakville', 'Aldershot'],
            'Aldershot GO': ['Port Credit', 'Oakville'],
            'Union Station': ['Oakville', 'Port Credit']
        }
    },
    '09': {
        'corridor': 'Lakeshore East',
        'directions_via': {
            'Oshawa GO': ['Danforth', 'Pickering', 'Ajax'],
            'Union Station': ['Ajax', 'Pickering', 'Danforth']
        }
    },
    '71': {
        'corridor': 'Stouffville',
        'directions_via': {
            'Lincolnville GO': ['Danforth', 'Kennedy', 'Markham', 'Stouffville']
        }
    },
    '21': {
        'corridor': 'Milton',
        'directions_via': {
            'Milton GO': ['Kipling', 'Cooksville', 'Meadowvale']
        }
    },
    '31': {
        'corridor': 'Kitchener',
        'directions_via': {
            'Kitchener GO': ['Bloor', 'Bramalea', 'Mount Pleasant'],
            'Mount Pleasant GO': ['Bloor', 'Bramalea']
        }
    },
    '61': {
        'corridor': 'Richmond Hill',
        'directions_via': {
            'Gormley GO': ['Oriole', 'Langstaff', 'Richmond Hill']
        }
    }
}


def line_via(line, destination):
    line_directions_vias = LINES[line]['directions_via']

    if destination not in line_directions_vias:
        print('destination {} not found for line {}, please add it!'.format(destination, line))
        return []
    else:
        return line_directions_vias[destination]


def parse_train(train):
    return {
        'trip_number': train.attrib['TripNumber'],
        'position': (float(train.attrib['Latitude']), float(train.attrib['Longitude'])),
        'moving': train.attrib['IsMoving'],
        'in_station': train.attrib.get('InStationId', None),
        'line': train.attrib['ServiceCd'],
        'from': train.attrib['StartStation'],
        'to': train.attrib['Destination'],
        'via': line_via(train.attrib['ServiceCd'], train.attrib['Destination'])
    }


def parse_line(line):
    r = requests.get(URL.format(line=line))
    xml = ET.fromstring(r.text)

    err_code = xml.attrib['ErrCode']

    if err_code != '0':
        raise ValueError('Error reported from GO Tracker service')

    data = xml[0]

    return [parse_train(train) for train in data]


def train_with_distance(train, loc):
    train['distance'] = math.sqrt(math.pow((train['position'][0] - loc[0]), 2) +
                                  math.pow((train['position'][1] - loc[1]), 2))

    return train


if __name__ == '__main__':
    all_trains = [
        train
        for line in LINES.keys()
        for train in parse_line(line)
    ]

    loc = (43.641, -79.417)

    trains_with_distance = [
        train_with_distance(train, loc)
        for train in all_trains
    ]

    sorted_trains = sorted(all_trains,
                           key=lambda t: t['distance']
                           )

    pprint(sorted_trains[:5])
