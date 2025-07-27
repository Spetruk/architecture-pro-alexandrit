from flask import Flask, jsonify
import os
import time
import random
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource

app = Flask(__name__)

# Configure OpenTelemetry
resource = Resource.create({"service.name": "price-service", "service.version": "1.0.0"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_AGENT_HOST", "simplest-agent"),
    agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

@app.route("/calculate", methods=["GET"])
def calculate_price():
    """
    Calculate jewelry price based on 3D model complexity
    This simulates the MES price calculation functionality
    """
    with tracer.start_as_current_span("calculate_jewelry_price") as span:
        try:
            # Add custom attributes
            span.set_attribute("calculation.type", "3d_jewelry")
            span.set_attribute("service.function", "price_calculation")
            
            # Simulate 3D model analysis
            with tracer.start_as_current_span("analyze_3d_model") as analysis_span:
                # Simulate different complexity levels
                complexity = random.choice(["simple", "medium", "complex"])
                polygon_count = random.randint(1000, 50000)
                
                analysis_span.set_attribute("model.complexity", complexity)
                analysis_span.set_attribute("model.polygon_count", polygon_count)
                
                # Simulate analysis time based on complexity
                analysis_time = {
                    "simple": random.uniform(0.1, 0.3),
                    "medium": random.uniform(0.5, 1.5),
                    "complex": random.uniform(2.0, 5.0)
                }[complexity]
                
                time.sleep(analysis_time)
                analysis_span.set_attribute("analysis.duration_seconds", analysis_time)
            
            # Simulate material cost calculation
            with tracer.start_as_current_span("calculate_material_cost") as material_span:
                material_type = random.choice(["silver", "gold", "platinum"])
                weight = random.uniform(5.0, 50.0)  # grams
                
                material_costs = {
                    "silver": 80,    # per gram
                    "gold": 4500,    # per gram  
                    "platinum": 3200  # per gram
                }
                
                material_cost = weight * material_costs[material_type]
                
                material_span.set_attribute("material.type", material_type)
                material_span.set_attribute("material.weight_grams", weight)
                material_span.set_attribute("material.cost_rub", material_cost)
                
                time.sleep(0.1)  # Simulate database lookup
            
            # Simulate labor cost calculation
            with tracer.start_as_current_span("calculate_labor_cost") as labor_span:
                complexity_multiplier = {
                    "simple": 1.0,
                    "medium": 1.5,
                    "complex": 2.5
                }[complexity]
                
                base_labor_hours = random.uniform(2, 8)
                total_labor_hours = base_labor_hours * complexity_multiplier
                hourly_rate = 2000  # RUB per hour
                labor_cost = total_labor_hours * hourly_rate
                
                labor_span.set_attribute("labor.base_hours", base_labor_hours)
                labor_span.set_attribute("labor.complexity_multiplier", complexity_multiplier)
                labor_span.set_attribute("labor.total_hours", total_labor_hours)
                labor_span.set_attribute("labor.cost_rub", labor_cost)
                
                time.sleep(0.05)
            
            # Calculate final price
            markup = 1.3  # 30% markup
            final_price = (material_cost + labor_cost) * markup
            
            result = {
                "price": round(final_price, 2),
                "currency": "RUB",
                "calculation_time": round(analysis_time, 2),
                "breakdown": {
                    "material_cost": round(material_cost, 2),
                    "labor_cost": round(labor_cost, 2),
                    "markup_percent": 30
                },
                "details": {
                    "complexity": complexity,
                    "material": material_type,
                    "weight_grams": round(weight, 2),
                    "labor_hours": round(total_labor_hours, 2),
                    "polygon_count": polygon_count
                }
            }
            
            # Add final attributes to main span
            span.set_attribute("price.final", final_price)
            span.set_attribute("price.material_cost", material_cost)
            span.set_attribute("price.labor_cost", labor_cost)
            span.set_attribute("calculation.success", True)
            
            return jsonify(result)
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            return jsonify({"error": "Price calculation failed", "details": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "price-service"})

if __name__ == "__main__":
    print("Starting Price Service...")
    print(f"Jaeger Agent: {os.getenv('JAEGER_AGENT_HOST', 'localhost')}:{os.getenv('JAEGER_AGENT_PORT', '6831')}")
    app.run(host="0.0.0.0", port=8080)
