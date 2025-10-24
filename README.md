# Python Push Interface

## Setup

1. Clone repo, cd into directory:

   ```bash
   git clone https://github.com/jasonbirchler/python-push-interface.git && cd push python-push-interface
   ```

1. Create virtual environment:

   ```bash
   python -m venv venv
   ```

1. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

1. You may need some system dependencies before ```pip install``` will work

   Raspbarry Pi:

   ```bash
   sudo apt install libcairo2-dev pkg-config python3-dev
   ```

   MacOS:

   ```bash
   brew install libcairo2-dev pkg-config python3-dev
   ```

   Windows: 🤷‍♂️

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

1. Run the project:

   ```bash
   python main.py
   ```

   Use the ```-s``` flag to start the simulator for local development w/o a Push attached:

   ```bash
   python main.py -s
   ```

You can stop the script with ```CTRL-c``` or when you're done, deactivate the Virtual Environment with:

```bash
deactivate
```

## Tests

### Running Tests

Run all tests:

```bash
python -m pytest tests/ -v
```

Run tests with coverage report:

```bash
python -m pytest tests/ --cov=. --cov-report=html
```

Run specific test files:

```bash
python -m pytest tests/test_sequencer.py -v
python -m pytest tests/test_handlers/ -v
```

Run tests quietly (just pass/fail count):

```bash
python -m pytest tests/ -q
```

### Test Structure

- `tests/test_sequencer.py` - Core sequencer logic and patterns
- `tests/test_midi_output.py` - MIDI communication and port management
- `tests/test_device_manager.py` - Device discovery and CC mapping
- `tests/test_project_manager.py` - Project save/load functionality
- `tests/test_handlers/` - User interface handlers (transport, track, device, clock, encoder)

Tests use mocking to simulate hardware dependencies (Push 2, MIDI devices) so they can run without physical hardware.
