"""
Mock Payment Microservice using Flask
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from logger import Logger
from flask import Flask, request, jsonify
from controllers.payment_controller import add_payment, process_payment, get_payment
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

app = Flask(__name__)
logger = Logger.get_instance("payments")

# --- Distributed tracing (Jaeger via OpenTelemetry) ---
resource = Resource.create({
    "service.name": "payments-api",
    "service.version": "1.0.0"
})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Jaeger reçoit les traces en OTLP/gRPC sur le port 4317 (hostname "jaeger" dans Docker)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"),
    insecure=True
)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# Instrumentation automatique : un span par requête Flask reçue,
# et propagation du contexte (en-tête traceparent) dans chaque appel requests sortant
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

@app.route("/")
def home():
    """Handle requests to base URL of the microservice """
    return jsonify({"service": "PaymentMicroservice", "status": "running"})

@app.route("/payments", methods=["POST"])
def post_add_payment():
    """Create a new payment"""
    logger.debug("Endpoint: POST /payments")
    with tracer.start_as_current_span("create-payment") as span:
        try:
            result = add_payment(request)
            span.set_attribute("payment.id", result.get("payment_id", 0))
            return jsonify(result), 201
        except Exception as e:
            span.record_exception(e)
            return jsonify({"error": str(e)}), 400

@app.route("/payments/process/<int:payment_id>", methods=["POST"])
def post_process_payment(payment_id):
    """Process a simulated credit card payment"""
    logger.debug(f"Endpoint: POST /payments/process/{payment_id}")
    with tracer.start_as_current_span("process-payment") as span:
        span.set_attribute("payment.id", payment_id)
        try:
            credit_card_data = request.get_json() or {}
            result = process_payment(payment_id, credit_card_data)
            return jsonify(result)
        except Exception as e:
            span.record_exception(e)
            return jsonify({"error": str(e)}), 400
    
@app.route("/payments/<int:payment_id>", methods=["GET"])
def get_payment_details(payment_id):
    """Get payment details for a specific payment ID"""
    with tracer.start_as_current_span("get-payment") as span:
        span.set_attribute("payment.id", payment_id)
        try:
            payment_data = get_payment(payment_id)
            return jsonify(payment_data)
        except Exception as e:
            span.record_exception(e)
            return jsonify({"error": str(e)}), 404

@app.errorhandler(404)
def handle_404(error):
    """Handle 404 errors with JSON response"""
    logger.error(error)
    return jsonify({"error": "Endpoint ou ressource introuvable"}), 404

# Start Flask app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5009, debug=True)