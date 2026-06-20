"""The host hook surface — an event dispatcher behind one console script (D-025).

``dispatch.main`` reads the host's hook payload from stdin and routes on
``hook_event_name`` to a read-only handler in ``handlers`` (SessionStart digest,
PreCompact flush-reminder, PostCompact re-digest, UserPromptSubmit auto-analyze).
Every handler is read-only and the dispatcher always exits 0 (INVARIANT-04/06).
``sessionstart`` remains as a back-compat shim.
"""
