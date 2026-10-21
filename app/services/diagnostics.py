"""Synthetic operations used to review responsiveness without opening devices."""
from app.services.tasks import TaskContext


def run_diagnostic(context: TaskContext, *, fail=False):
    for step in range(1, 61):
        context.checkpoint()
        context.pause(.05)
        context.progress(round(step * 100 / 60))
    if fail:
        raise RuntimeError("Synthetic diagnostic failure")
    return "Pemeriksaan selesai. Aplikasi tetap merespons selama proses berjalan."
