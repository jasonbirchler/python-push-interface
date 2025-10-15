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
