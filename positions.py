import position_go
import position_upx
import position_via


def build_geojson(trains_list):
    collection = {"type": "FeatureCollection", "features": []}

    for train in trains_list:
        result = {"type":"Feature", "properties":dict(train),
                  "geometry":{"type":"Point","coordinates":[train['position'][1], train['position'][0]]}}
        collection['features'].append(result)

    return collection

def collect_trains():
    go_trains = position_go.all_trains()
    upx_trains = position_upx.get_current_train_positions()
    via_trains = position_via.parse_trains()

    local_via_trains = [train for train in via_trains
                        if -81 > train['position'][1] > -78]

    return go_trains + upx_trains + local_via_trains


def trains_as_geojson():
    return build_geojson(collect_trains())
