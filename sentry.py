import sentry_sdk

def init_sentry(dsn:str|None):
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.2,
            profiles_sample_rate=0.1,
        )
