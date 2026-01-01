"""Issue tracker integrations for Amelia.

Provide adapters for fetching issue data from various project management
systems. Each tracker implements the BaseTracker protocol to normalize
issue data for the orchestrator.

Exports:
    BaseTracker: Protocol defining the tracker interface (via base module).
    GithubTracker: Tracker for GitHub Issues (via github module).
    JiraTracker: Tracker for Atlassian Jira (via jira module).
    NoopTracker: No-op tracker for standalone usage (via noop module).
    create_tracker: Factory function for tracker instantiation (via factory module).
"""
