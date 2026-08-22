from textual.command import DiscoveryHit, Hit, Hits, Provider


class LoadPresetProvider(Provider):
    """A provider to open LoadPresetScreen."""

    async def discover(self) -> Hits:
        app = self.app
        assert hasattr(app, "load_preset"), "The App must implement: 'load_preset'"

        command = "Load Preset"
        yield DiscoveryHit(
            command,
            app.load_preset,  # pyright: ignore[reportAttributeAccessIssue]
            help="Load keys from a preset",
        )

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)

        app = self.app
        assert hasattr(app, "load_preset"), "The App must implement: 'load_preset'"

        command = "Load Preset"
        score = matcher.match(command)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(command),
                app.load_preset,  # pyright: ignore[reportAttributeAccessIssue]
                help="Load keys from a preset",
            )
