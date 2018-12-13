from collections import defaultdict
import csv
from datetime import datetime
import math
from pprint import pprint


def train_with_distance(train, loc):
    train['distance'] = math.sqrt(math.pow((train['position'][0] - loc[0]), 2) +
                                  math.pow((train['position'][1] - loc[1]), 2))

    return train


def parse_gtfs_time(gtfs_time):
    hours, minutes, seconds = gtfs_time.split(':')

    if int(hours) > 23:
        hours = hours - 24

    today = datetime.today()
    # TODO: tzinfo?
    return datetime(today.year, today.month, today.day,
                    int(hours), int(minutes), int(seconds))


def add_position(trip, now, now_str, all_shapes):
    # find the two stops the train is between
    # and extrapolate train position based on it.
    # extrapolate where on shape we should be from time

    shape = all_shapes[trip['shape_id']]

    # handle holding at stations:
    # the train might depart Weston at 12:08, arrive Bloor 12:12,
    # depart Bloor 12:14, arrive Union 12:22. At 12:13 it is _after_
    # departure from Weston, but also _after_ arrival at Bloor.
    at_station = [
        stop for stop in trip['stops']
        if stop['arrival_time'] <= now_str <= stop['departure_time']
    ]

    if at_station:
        current_dist_travelled = float(at_station[0]['shape_dist_traveled'])
    else:
        # estimate where we are between stations, assuming linear speed between them

        station_before_now = [
            stop for stop in trip['stops']
            if stop['departure_time'] <= now_str
        ][-1]
        station_after_now = [
            stop for stop in trip['stops']
            if stop['arrival_time'] >= now_str
        ][0]

        # parse times, see how far we are between stations
        time_departed = parse_gtfs_time(station_before_now['departure_time'])
        time_arriving = parse_gtfs_time(station_after_now['arrival_time'])
        leg_duration = time_arriving - time_departed
        leg_percent = (now - time_departed).total_seconds() / leg_duration.total_seconds()
        current_dist_travelled = float(station_before_now['shape_dist_traveled']) + (
            (float(station_after_now['shape_dist_traveled'])
             - float(station_before_now['shape_dist_traveled']))
            * leg_percent)

    position_before_now = [
        point for point in shape
        if float(point['shape_dist_traveled']) <= current_dist_travelled
    ][-1]

    position_after_now = [
        point for point in shape
        if float(point['shape_dist_traveled']) >= current_dist_travelled
    ][0]

    found_position = (
        (float(position_before_now['shape_pt_lat'])
         + float(position_after_now['shape_pt_lat']))/2,
        (float(position_before_now['shape_pt_lon']) +
         float(position_after_now['shape_pt_lon']))/2
    )

    trip['position'] = found_position

    return trip


def get_current_train_positions():
    # load from GTFS
    # first, shapes
    all_shapes = defaultdict(list)
    with open('shapes.txt', encoding='utf-8-sig') as f:
        shapes_reader = csv.DictReader(f)

        for shape_point in shapes_reader:
            all_shapes[shape_point['shape_id']].append(shape_point)

    # then trips, including their stop_times
    # in this particular case the GTFS files only include one route and it's the UPX

    # first, load the stop_times for the trips
    all_stop_times = defaultdict(list)
    with open('stop_times.txt', encoding='utf-8-sig') as f:
        stop_times = csv.DictReader(f)

        for stop_time in stop_times:
            all_stop_times[stop_time['trip_id']].append(stop_time)

    # oddity: stop_times per trip in UPX GTFS are specified in reverse order,
    # so we have to sort by stop_sequence
    all_stop_times = {
        trip_id: sorted(stop_times, key=lambda s: s['stop_sequence'])
        for trip_id, stop_times in all_stop_times.items()
    }

    with open('trips.txt', encoding='utf-8-sig') as f:
        trips_reader = csv.DictReader(f)

        # TODO: also take into account service_id mapped to calendar...
        all_trips = [
            {
                'trip_number': trip['trip_id'],
                'to': trip['trip_headsign'],
                'shape_id': trip['shape_id'],
                'stops': all_stop_times[trip['trip_id']]
            }
            for trip in trips_reader
            if trip['service_id'] == '9204'  # TODO: un-hard-code
        ]

    # Only include trips that have first stop_time before now
    # and last stop_time after now.
    # GTFS time format is like "05:55:00", so string comparisons will work.
    # GTFS times after midnight are like "25:25:00"; UPX has no service
    # before 4 a.m., so force times before 4:00 to be previous day.
    now = datetime.now()  # TODO: double-check the timezone!
    if now.hour > 3:
        now_str = datetime.now().strftime('%H:%M:%S')
    else:
        now_str = str(now.hour + 24) + datetime.now().strftime(':%M:%S')

    current_trips = [trip for trip in all_trips
                     if trip['stops'][0]['departure_time'] <= now_str
                     and trip['stops'][-1]['arrival_time'] >= now_str]

    trips_with_positions = [add_position(trip, now, now_str, all_shapes)
                            for trip in current_trips]

    return trips_with_positions


if __name__ == '__main__':
    trains = get_current_train_positions()

    loc = (43.641, -79.417)

    trains_with_distance = [
        train_with_distance(train, loc)
        for train in trains
    ]

    sorted_trains = sorted(trains, key=lambda t: t['distance'])

    pprint(sorted_trains[:5])
