from textual.command import DiscoveryHit, Hit, Hits, Provider


class SavePresetProvider(Provider):
    async def discover(self) -> Hits:
        app = self.app
        assert hasattr(app, "save_preset"), "The App must implement: 'save_preset'"

        command = "Save Preset"
        yield DiscoveryHit(
            command,
            app.save_preset,  # pyright: ignore[reportAttributeAccessIssue]
            help="Save current keys to a preset",
        )

    async def search(self, querry: str) -> Hits:
        """Called on each key-press in the Command Palette"""
        matcher = self.matcher(querry)

        app = self.app
        assert hasattr(app, "save_preset"), "The App must implement: 'save_preset'"

        command = "Save Preset"
        score = matcher.match(command)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(command),
                app.save_preset,  # pyright: ignore[reportAttributeAccessIssue]
                help="Save current keys to a preset",
            )
