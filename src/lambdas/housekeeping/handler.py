from ...common.logging import logger
def lambda_handler(event, context):
    # TODO Etap 2: retention and GDPR delete
    logger.info({"housekeeping": "noop"})
    return {"statusCode": 200}
