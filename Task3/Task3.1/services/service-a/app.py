from flask import Flask, jsonify
import requests
import os
import time
import random
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource

app = Flask(__name__)

# Configure OpenTelemetry
resource = Resource.create({"service.name": "order-service", "service.version": "1.0.0"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "simplest-agent"),
    agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument Flask and Requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

PRICE_SERVICE_URL = os.getenv("PRICE_SERVICE_URL", "http://service-b:8080")

@app.route("/", methods=["GET"])
def process_order():
    """
    Process jewelry order - calculates price and creates order
    This endpoint simulates the Alexandrite order processing flow
    """
    with tracer.start_as_current_span("process_order") as span:
        # Add custom attributes to span
        order_id = f"order-{random.randint(1000, 9999)}"
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.type", "custom_jewelry")
        span.set_attribute("customer.segment", "B2C")
        
        try:
            # Simulate order validation
            with tracer.start_as_current_span("validate_order") as validation_span:
                validation_span.set_attribute("validation.result", "success")
                time.sleep(0.1)  # Simulate validation time
            
            # Call price service to calculate jewelry price
            with tracer.start_as_current_span("call_price_service") as price_span:
                price_span.set_attribute("service.name", "price-service")
                price_span.set_attribute("jewelry.complexity", "medium")
                
                try:
                    response = requests.get(f"{PRICE_SERVICE_URL}/calculate", timeout=5)
                    response.raise_for_status()
                    price_data = response.json()
                    
                    price_span.set_attribute("price.calculated", price_data.get("price", 0))
                    price_span.set_attribute("http.status_code", response.status_code)
                    
                except requests.exceptions.RequestException as e:
                    price_span.set_attribute("error", True)
                    price_span.set_attribute("error.message", str(e))
                    raise
            
            # Simulate order creation
            with tracer.start_as_current_span("create_order") as create_span:
                create_span.set_attribute("order.status", "PRICE_CALCULATED")
                time.sleep(0.05)  # Simulate database write
            
            result = {
                "order_id": order_id,
                "status": "PRICE_CALCULATED",
                "price": price_data.get("price", 0),
                "calculation_time": price_data.get("calculation_time", 0),
                "currency": "RUB",
                "estimated_delivery": "21 days",
                "next_step": "Waiting for customer approval"
            }
            
            span.set_attribute("order.final_price", result["price"])
            span.set_attribute("order.status", "completed")
            
            return jsonify(result)
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            return jsonify({"error": "Failed to process order", "details": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "order-service"})

if __name__ == "__main__":
    print("Starting Order Service...")
    print(f"Price Service URL: {PRICE_SERVICE_URL}")
    print(f"Jaeger Agent: {os.getenv('JAEGER_AGENT_HOST', 'localhost')}:{os.getenv('JAEGER_AGENT_PORT', '6831')}")
    app.run(host="0.0.0.0", port=8080)
