from multiprocessing import Pool, TimeoutError
import sys

import position_go
import position_upx
import position_via


def collect_trains():
    # get the train positions in parallel
    train_getters = [
        position_go.all_trains,
        position_upx.get_current_train_positions,
        position_via.parse_trains,
        ]

    with Pool() as pool:
        task_list = [(task, pool.apply_async(task))
                     for task in train_getters]
        results = []
        for task, task_result in task_list:
            try:
                results.extend(task_result.get(timeout=1))
            except TimeoutError:
                # log and ignore
                print("Timed out on " + str(task), file=sys.stderr)
                pass

    # filter out VIA trains outside GTA
    local_results = [train for train in results
                     if -81 < train['position'][1] < -78]

    return local_results


def build_train_geojson(train):
    return {
        "type": "Feature",
        "properties": train,
        "geometry": {
            "type": "Point",
            "coordinates": [train['position'][1], train['position'][0]]
        }
    }


def build_geojson(trains_list):
    return {
        "type": "FeatureCollection",
        "features": [build_train_geojson(train) for train in trains_list]
    }


def trains_as_geojson():
    return build_geojson(collect_trains())
