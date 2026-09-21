"""Twenty earlier exchanges, none overlapping the test cases.

Each pair is (user request, assistant reply with a body). The clean version
moves the body text into the user turn, so the two histories carry the same
characters and differ only in the shape of the assistant's own output.
"""

INDUCTION = [
    ("cache user sessions in redis",
     "feat(session): store sessions in redis\n\nSessions were held in process memory and lost on restart.\nThey now persist in redis with a 30 day expiry."),
    ("fix the off by one in pagination",
     "fix(pagination): correct last page boundary\n\nThe final page dropped one row when the total was an exact\nmultiple of the page size."),
    ("add retry logic to the webhook sender",
     "feat(webhooks): retry failed deliveries\n\nAdds three retries with exponential backoff.\nPermanent failures are written to the dead letter table."),
    ("delete the old migration scripts",
     "chore(db): remove pre-2024 migrations\n\nThese were squashed into the baseline schema last quarter\nand have not run since."),
    ("switch logging from print to structlog",
     "refactor(logging): move to structlog\n\nReplaces print calls across the ingest package.\nLog lines are now JSON and carry a request id."),
    ("handle null values in the export",
     "fix(export): write empty string for nulls\n\nNull values previously serialised as the literal None.\nDownstream parsers rejected those rows."),
    ("add an index on orders.created_at",
     "perf(db): index orders.created_at\n\nThe daily report scanned the full table.\nQuery time drops from 8s to under 200ms."),
    ("update the CI image to python 3.13",
     "ci(actions): upgrade to python 3.13\n\nBumps the runner image and pins setuptools.\nTwo deprecation warnings are now errors."),
    ("rename the customer_id column to account_id",
     "refactor(schema): rename customer_id to account_id\n\nMatches the naming used everywhere else in the service.\nA view keeps the old name available for one release."),
    ("add a health check endpoint",
     "feat(api): add /healthz endpoint\n\nReturns 200 when the database and cache both answer.\nUsed by the load balancer."),
    ("stop logging the auth header",
     "fix(logging): redact the authorization header\n\nRequest logs included bearer tokens in full.\nThe header is now replaced with a fixed placeholder."),
    ("batch the inserts in the loader",
     "perf(loader): insert rows in batches of 500\n\nThe loader issued one statement per row.\nA nightly load drops from 40 minutes to under 4."),
    ("pin the numpy version",
     "chore(deps): pin numpy below 3.0\n\nThe 3.0 release removes np.float_.\nPinning buys time to migrate the calling code."),
    ("add a timeout to the http client",
     "fix(client): add a 10 second request timeout\n\nRequests could hang until the worker was recycled.\nThey now fail fast and retry."),
    ("move the config to environment variables",
     "refactor(config): read settings from the environment\n\nSettings were hardcoded in a module.\nThey are now read once at startup and validated."),
    ("drop support for python 3.9",
     "chore(python): drop 3.9 support\n\n3.9 reached end of life in October.\nThe test matrix now starts at 3.10."),
    ("fix the flaky scheduler test",
     "test(scheduler): freeze time in the interval test\n\nThe test compared wall clock timestamps and failed near\nmidnight. It now uses a fixed clock."),
    ("compress the API responses",
     "perf(api): gzip responses over 1KB\n\nAdds compression middleware.\nThe largest listing endpoint drops from 900KB to 70KB."),
    ("validate the upload file type",
     "feat(upload): reject files that are not CSV\n\nAny content type was accepted and failed later in parsing.\nThe check now happens at the boundary."),
    ("document the retry behaviour",
     "docs(webhooks): describe the retry schedule\n\nThe retry counts and backoff were only visible in code.\nThey are now in the integration guide."),
]
