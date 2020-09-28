Tools for TagTime/Beeminder integration.

## Scripts

Setup:
```bash
mkdir -p ~/.config/beetime
cp example-config.json ~/.beetime/config.json  # and fix the credentials
cp example-scorers.py ~/.beetime/scorers.py    # and write your custom ping-scoring logic
```

Then:
- `python -m beetime.scripts.sync_attachments` will search your email inbox for any attachments from your configured sender, score the pings from any new `timepie.log` files, and send those scores to Beeminder.

## Development

To ramp up quickly: look at `scripts/sync_attachments.py`. The core logic is in `find_timepie_attachments` and `client.sync`.

To test:

```bash
mypy beetime/ && pytest
```