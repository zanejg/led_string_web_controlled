# LED String Controller - Threading Implementation

## Overview
The LED controller now uses **threading with event control** to run effects continuously in the background while the Flask app responds to HTTP requests.

## How It Works

### Architecture
1. **Main Thread**: Runs the Flask web server
2. **Effect Thread**: Runs the LED effect in the background (daemon thread)
3. **stop_event**: A `threading.Event` that signals when to stop the current effect

### Key Components

#### In `main.py`:
- `effect_thread`: Global variable holding the current effect thread
- `stop_event`: Threading event to signal stop
- `current_effect`: Name of the currently running effect
- `thread_lock`: Lock to prevent race conditions

#### Helper Functions:
- `stop_current_effect()`: Stops the currently running effect cleanly
- `start_effect(name, function, *args, **kwargs)`: Starts a new effect (stops current one first)

#### Modified Effect Functions in `various_effects.py`:
All effect functions now accept a `stop_event` parameter and check it regularly:
- `flame.run(stop_event=None)`
- `expanding_waves.run(stop_event=None)`
- `heart_beat(strip, color1, color2, stop_event=None)`

## API Endpoints

### Start Effects
```bash
# Start heartbeat effect (runs continuously)
curl http://localhost:5000/control_led/heart

# Start expanding waves effect
curl http://localhost:5000/control_led/wave

# Start flame effect
curl http://localhost:5000/control_led/flame

# Start audio loudness effect (reacts to overall volume)
curl http://localhost:5000/control_led/audio_loudness

# Start audio frequency effect (reacts to different frequency bands)
curl http://localhost:5000/control_led/audio_frequency

# Stop current effect and turn off LEDs
curl http://localhost:5000/control_led/stop
```

### Check Status
```bash
# Get current status
curl http://localhost:5000/api/status

# Response:
{
  "status": "ok",
  "message": "Flask app is running",
  "current_effect": "heartbeat",
  "effect_running": true
}
```

### List Available Effects
```bash
curl http://localhost:5000/api/effects

# Response:
{
  "status": "success",
  "effects": ["heart", "wave", "flame", "audio_loudness", "audio_frequency", "stop"]
}
```

## How Effects Run Continuously

### Before (Duration-Based):
```python
def run(self, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        # do effect
        time.sleep(0.1)
```

### After (Event-Based):
```python
def run(self, stop_event=None):
    while not (stop_event and stop_event.is_set()):
        # do effect
        time.sleep(0.1)
        # Effect stops when stop_event is set from Flask
```

## Switching Between Effects

When you trigger a new effect:
1. Flask receives the request
2. `start_effect()` is called
3. Current effect's `stop_event` is set
4. Current thread exits gracefully (within 2 seconds)
5. New effect thread starts
6. New effect runs continuously until stopped

## Running the Application

```bash
# Navigate to the app directory
cd /home/zane/remote/ledpi/led_string_web_controlled/app

# Run the Flask app
python main.py

# The app will:
# - Start Flask on 0.0.0.0:5000
# - Initialize the LED strip
# - Wait for commands
# - Clean up LEDs on exit
```

## Example Usage Sequence

```bash
# 1. Start the server
python main.py

# 2. In another terminal or browser, trigger effects:
curl http://localhost:5000/control_led/heart
# Heartbeat effect starts and runs continuously...

# 3. Switch to another effect (heartbeat stops automatically)
curl http://localhost:5000/control_led/wave
# Wave effect starts...

# 4. Stop all effects
curl http://localhost:5000/control_led/stop
# All LEDs turn off

# 5. Check what's running
curl http://localhost:5000/api/status
```

## Adding New Effects

To add a new effect:

1. **In `various_effects.py`**, modify your effect to accept `stop_event`:
```python
def my_new_effect(strip, color, stop_event=None):
    """My new effect that runs continuously."""
    while not (stop_event and stop_event.is_set()):
        # Your effect code here
        strip.setPixelColor(0, color)
        strip.show()
        time.sleep(0.1)
```

2. **In `main.py`**, add a new case to `control_led()`:
```python
case "myneweffect":
    start_effect(
        'my_new_effect',
        ve.my_new_effect,
        strip,
        Color(255, 0, 0),
        stop_event
    )
```

3. **Update the `/api/effects` endpoint** to include the new effect name.

## Thread Safety

- Uses `thread_lock` to prevent race conditions
- Only one effect runs at a time
- Daemon threads ensure clean shutdown
- `atexit` handler ensures LEDs turn off on exit

## Benefits of This Approach

✅ Effects run continuously until stopped
✅ Easy to switch between effects
✅ Clean shutdown and cleanup
✅ No blocking of Flask server
✅ Simple to understand and extend
✅ Thread-safe with locks
✅ LEDs turn off automatically on exit
