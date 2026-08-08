from textual.command import DiscoveryHit, Hit, Hits, Provider


class OpenListenerProvider(Provider):
    async def discover(self) -> Hits:
        app = self.app
        assert hasattr(app, "open_listener"), "The App must implement: 'open_listener'"

        command = "Open Listener"
        yield DiscoveryHit(
            command,
            app.open_listener,  # pyright: ignore[reportAttributeAccessIssue]
            help="Open a listener to receive keys from other programs",
        )

    async def search(self, query: str) -> Hits:
        """Called on each key-press in the Command Palette"""
        matcher = self.matcher(query)

        app = self.app
        assert hasattr(app, "open_listener"), "The App must implement: 'open_listener'"

        command = "Open Listener"
        score = matcher.match(command)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(command),
                app.open_listener,  # pyright: ignore[reportAttributeAccessIssue]
                help="Open a listener to receive keys from other programs",
            )
