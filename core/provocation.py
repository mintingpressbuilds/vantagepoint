from core.session import VPSession
from core.mode import Mode


def start_session(friction):
    """Create session from initial friction statement."""
    session = VPSession(friction=friction)
    return session


def calibrate(session, what_wrong, how_long, what_right):
    """Run calibration questions. Returns verified friction statement."""
    session.calibration = {
        "what_wrong": what_wrong,
        "how_long": how_long,
        "what_right": what_right,
    }
    # Build verified friction statement
    session.friction_statement = (
        f"Friction: {session.friction}. "
        f"Specifically: {what_wrong}. "
        f"Duration: {how_long}. "
        f"Target state: {what_right}."
    )
    session.chain_entries.append({
        "phase": "provocation",
        "action": "calibrated",
        "data": session.calibration,
        "output": session.friction_statement,
    })
    return session


def complete_provocation(session):
    """Verify friction statement and advance to expedition."""
    if not session.friction_statement:
        raise ValueError("Must calibrate before completing provocation")
    session.advance_phase("expedition")
    return session
