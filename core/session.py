import uuid
from datetime import datetime
from core.mode import detect_mode


class VPSession:
    def __init__(self, friction=None):
        self.id = str(uuid.uuid4())
        self.mode = detect_mode()
        self.created_at = datetime.utcnow().isoformat()
        self.phase = "provocation"
        self.friction = friction

        # Provocation output
        self.friction_statement = None
        self.calibration = {}           # what_wrong, how_long, what_right

        # Expedition output
        self.territory = {
            "nodes": [],                # { id, label, type: ground|convention|unknown, significance: float }
            "edges": [],                # { source, target, label }
            "clusters": [],             # { id, label, node_ids }
        }
        self.discoveries = []           # { finding, significance, verified: bool }
        self.assumptions = []           # { statement, classification: ground|convention, evidence }
        self.threshold = 0.0            # 0.0 to 1.0 — ground made vs ground remaining

        # Vantage output
        self.goal = None                # Verified goal statement
        self.vantage_summary = None     # What can be seen from here

        # Paths output
        self.paths = []                 # [ { path_id, label, description, gap_score, assumptions, confidence, risk } ]
        self.chosen_path = None

        # Doorway results (Mode 2 only)
        self.doorway_results = []       # Raw results from doorway /run calls

        # Chain
        self.chain_entries = []         # Every state transition logged

    def advance_phase(self, next_phase):
        valid_transitions = {
            "provocation": "expedition",
            "expedition": "vantage",
            "vantage": "paths",
            "paths": "receipt",
        }
        expected = valid_transitions.get(self.phase)
        if expected != next_phase:
            raise ValueError(f"Cannot go from {self.phase} to {next_phase}. Expected: {expected}")
        self.phase = next_phase

    def to_dict(self):
        return {
            "id": self.id, "mode": self.mode, "phase": self.phase,
            "created_at": self.created_at, "friction": self.friction,
            "friction_statement": self.friction_statement,
            "calibration": self.calibration, "territory": self.territory,
            "discoveries": self.discoveries, "assumptions": self.assumptions,
            "threshold": self.threshold, "goal": self.goal,
            "vantage_summary": self.vantage_summary, "paths": self.paths,
            "chosen_path": self.chosen_path, "chain_entries": self.chain_entries,
        }
