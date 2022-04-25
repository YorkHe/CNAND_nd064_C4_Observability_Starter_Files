import imp
import logging
import opentracing

from flask import Flask, render_template, request, jsonify

import pymongo
from flask_pymongo import PyMongo
from flask_opentracing import FlaskTracing

from jaeger_client import Config
from jaeger_client.metrics.prometheus import PrometheusMetricsFactory
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

app.config["MONGO_DBNAME"] = "backendDB"
app.config[
    "MONGO_URI"
] = "mongodb://adminuser:password123@mongo-nodeport-svc:27017/backendDB?authSource=admin"

mongo = PyMongo(app)

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

metrics = PrometheusMetrics(app)
metrics.info("app_info", "Application info", app_name="backend")

config = Config(
    config={
        "sampler": {"type": "const", "param": 1},
        "logging": True,
        "reporter_batch_size": 1
    },
    service_name="backend",
    validate=True,
    metrics_factory=PrometheusMetricsFactory(service_name_label="backend"),
)

tracer = config.initialize_tracer()
flask_tracer = FlaskTracing(tracer, True, app)

@app.route("/")
@metrics.counter(
    'cnt_homepage', 'Number of invocations of homepage',
    labels={
        'status': lambda resp: resp.status_code
    }
)
def homepage():
    return "Hello World"


@app.route("/api")
@metrics.counter(
    'cnt_api', 'Number of invocations of api',
    labels={
        'status': lambda resp: resp.status_code
    }
)
def my_api():
    answer = "something"
    return jsonify(repsonse=answer)


@app.route("/star", methods=["POST"])
@metrics.counter(
    'cnt_star', 'Number of invocations of star',
    labels={
        'status': lambda resp: resp.status_code
    }
)
def add_star():
    with flask_tracer.tracer.start_span("add-star") as span:
        star = mongo.db.get_collection("stars")
        name = request.json["name"]
        distance = request.json["distance"]
        span.log_kv({"event": "add star", "name":name, "distance":distance})

        with flask_tracer.tracer.start_span("request-mongo") as mongo_span:
            star_id = star.insert({"name": name, "distance": distance})
            new_star = star.find_one({"_id": star_id})
            output = {"name": new_star["name"], "distance": new_star["distance"]}
            mongo_span.set_tag("star-id", star_id)

    return jsonify({"result": output})

if __name__ == "__main__":
    app.run()
