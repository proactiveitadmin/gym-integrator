from ..common.logging import logger
class MetricsService:
    def incr(self, name: str, **labels):
        logger.info({"metric": name, **labels})
