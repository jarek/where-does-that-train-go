import flask

import positions


app = flask.Flask(__name__)


@app.route("/trains.geojson")
def trains():
    return flask.json.jsonify(positions.trains_as_geojson())


if __name__ == "__main__":
    app.run()
