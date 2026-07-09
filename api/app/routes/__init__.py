"""Capability routers (S7): generation, action, reasoning.

Thin typed facades over the S6 job machinery (generation/action) + the streaming reasoner. Kept as a
leaf package — the route *builders* are imported directly by ``app.main`` (never re-exported here), so
``app.errors`` can import ``app.routes.checkpoint`` without pulling FastAPI/router construction.
"""
