from sequencer_app import SequencerApp
import sys

if __name__ == "__main__":
    use_simulator = '--simulator' in sys.argv or '-s' in sys.argv
    app = SequencerApp(use_simulator=use_simulator)
    app.run()
