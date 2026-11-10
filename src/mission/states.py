from mission.io import Outputs, Routine


def navigate() -> Routine:
    yield Outputs()
    return final


def final() -> Routine:
    """Since the state machine doesn't handle stopping, we can return this in order to effectively stop the machine"""
    yield Outputs(messages=["The final state has been reached"], motors=(0, 0))

    while True:
        yield Outputs()
