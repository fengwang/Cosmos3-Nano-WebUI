"""Edge modality preprocessors / validators (INV-6).

Pure, torch-free validation that runs at the API edge BEFORE any engine dispatch. Session 4 adds the
embodiment-schema validator; later sessions add the other modality validators here. Shared with S6/S7.
"""
