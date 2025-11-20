"""
LED String Web Controller - Flask Application

This Flask app controls LED effects using threading for continuous operation.

Threading Architecture:
- Effects run in background threads (daemon threads)
- stop_event (threading.Event) signals when to stop an effect
- Only one effect runs at a time
- Starting a new effect automatically stops the current one

API Endpoints:
- GET  /                      - Home page
- GET  /api/status            - Get current status and running effect
- GET  /api/effects           - List available effects
- GET  /api/set_color         - Set all LEDs to a solid color (param: color=#RRGGBB)
- GET  /control_led/<effect>  - Start an effect (heart, wave, flame, stop)

Usage:
- Visit http://your-pi-ip:5000/ to see the web interface
- Use /control_led/heart to start heartbeat effect
- Use /control_led/wave to start wave effect
- Use /control_led/flame to start flame effect
- Use /control_led/stop to stop all effects and turn off LEDs
"""

from flask import Flask, render_template, request, jsonify
from rpi_ws281x import *
import threading
import sys

import various_effects as ve
import audio_effects as ae


from four_meter import LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

background_color = Color(0,0,0)

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# Thread control variables
effect_thread = None
stop_event = threading.Event()
current_effect = None
thread_lock = threading.Lock()



def stop_current_effect():
    """Stop the currently running effect thread."""
    global effect_thread, stop_event, current_effect
    
    with thread_lock:
        if effect_thread and effect_thread.is_alive():
            stop_event.set()
            effect_thread.join(timeout=2.0)  # Wait up to 2 seconds for thread to finish
            if effect_thread.is_alive():
                print(f"Warning: Effect thread did not stop cleanly")
        
        effect_thread = None
        current_effect = None
        stop_event.clear()


def start_effect(effect_name, effect_function, *args, **kwargs):
    """Start a new effect in a background thread."""
    global effect_thread, current_effect
    
    print(f"start_effect called: {effect_name}")
    
    # Stop any currently running effect
    stop_current_effect()
    
    with thread_lock:
        current_effect = effect_name
        effect_thread = threading.Thread(
            target=effect_function,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        effect_thread.start()
        print(f"Thread started for {effect_name}, thread alive: {effect_thread.is_alive()}")


@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """API endpoint to get current status"""
    return jsonify({
        'status': 'ok',
        'message': 'Flask app is running',
        'current_effect': current_effect,
        'effect_running': effect_thread.is_alive() if effect_thread else False
    })


@app.route('/api/data', methods=['POST'])
def post_data():
    """API endpoint to receive data"""
    data = request.get_json()
    # Process your data here
    return jsonify({
        'status': 'success',
        'received': data
    })


@app.route('/control_led/<led_id>', methods=['GET'])
def control_led(led_id):
    """API endpoint to control a specific LED"""
    data = request.args
    print(f"Received request for effect: {led_id}")
    
    # Control the LED here using the data

    match led_id:
        case 'heart':
            print("Starting heartbeat effect...")
            start_effect(
                'heartbeat',
                ve.heart_beat,
                strip,
                ve.NEGATIVE_BEAT_COLOUR,
                ve.POSITIVE_BEAT_COLOUR,
                stop_event
            )
        case "wave":
            print("Starting wave effect...")
            ex_wave = ve.expanding_waves(strip, 0.5, 
                                         ve.BACKCOLOUR, 
                                         ve.OUTER_FLAME_COLOUR)
            start_effect('expanding_waves', ex_wave.run, stop_event)
        case "flame":
            print("Starting flame effect...")
            flame_effect = ve.flame(strip, ve.BACKCOLOUR, 
                                    ve.OUTER_FLAME_COLOUR, 
                                    ve.INNER_FLAME_COLOUR)
            start_effect('flame', flame_effect.run, stop_event)
        case "audio_loudness":
            print("Starting audio loudness effect...")
            ae.clear_audio_buffer()  # Clear any pending audio data
            loudness_controller = ae.create_loudness_controller(strip)
            start_effect('audio_loudness', loudness_controller.run, stop_event)
        case "audio_frequency":
            print("Starting audio frequency effect...")
            ae.clear_audio_buffer()  # Clear any pending audio data
            frequency_controller = ae.create_frequency_controller(strip)
            start_effect('audio_frequency', frequency_controller.run, stop_event)
        case "stop":
            print("Stopping all effects...")
            stop_current_effect()
            ve.set_all(strip, Color(0, 0, 0))  # Turn off all LEDs
            return jsonify({
                'status': 'success',
                'action': 'stopped',
                'effect': 'none'
            })
        case _:
            print(f"Unknown effect: {led_id}")
            return jsonify({
                'status': 'error',
                'message': f'Unknown effect: {led_id}'
            }), 400

    return jsonify({
        'status': 'success',
        'led_id': led_id,
        'action': data.get('action'),
        'effect': current_effect
    })


@app.route('/api/effects', methods=['GET'])
def list_effects():
    """API endpoint to list available effects"""
    return jsonify({
        'status': 'success',
        'effects': ['heart', 'wave', 'flame', 'audio_loudness', 'audio_frequency', 'stop']
    })


@app.route('/api/set_color', methods=['GET'])
def set_color():
    """API endpoint to set all LEDs to a solid color"""
    color_hex = request.args.get('color', '#000000')
    print(f"Setting solid color: {color_hex}")
    
    try:
        # Stop any running effects first
        stop_current_effect()
        
        # Convert hex color to RGB
        color_hex = color_hex.lstrip('#')
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        
        # Set all LEDs to the chosen color
        color = Color(r, g, b)
        ve.set_all(strip, color)
        
        return jsonify({
            'status': 'success',
            'color': f'#{color_hex}',
            'rgb': {'r': r, 'g': g, 'b': b}
        })
    except Exception as e:
        print(f"Error setting color: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


def cleanup():
    """Cleanup function to stop effects and turn off LEDs when app exits."""
    stop_current_effect()
    ae.close_audio_stream()  # Close audio stream if it was opened
    ve.set_all(strip, Color(0, 0, 0))
    print("LED strip cleaned up and turned off")


if __name__ == '__main__':
    import atexit
    import signal
    
    # Register cleanup for normal exit
    atexit.register(cleanup)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nShutting down gracefully...")
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)

    ve.colorWipe(strip, Color(255, 255, 0), 10)  # Ensure LEDs are off at start
    ve.colorWipe(strip, Color(0, 0, 0), 10)  # Ensure LEDs are off at start
    
    # Run Flask without the reloader in debug mode to avoid process complications
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
