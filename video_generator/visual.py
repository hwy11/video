"""Video clip generation and visual effects."""
from typing import List, Dict


def create_video_clips(timeline: List[Dict], config: Dict):
    """Create video clips for each timeline entry applying visual effects.

    The typical effect is a Ken Burns pan/zoom defined by ``config``. This
    function should return a list of ``moviepy`` clips.
    """
    raise NotImplementedError("Video clip creation not implemented.")
