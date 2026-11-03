"""Adapters that turn a harness's own records into Inspect `CommunicationEvent`s.

Each adapter takes the sample store, as replayed from `StoreEvent`s, and returns
`CommunicationEvent`-shaped dicts, or `None` when the store is not from its harness.
"""
