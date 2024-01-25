import logging
from datetime import datetime

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the desired logging level

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Set the desired logging level for console output

# Create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)

class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Check if request has a user attribute
            if hasattr(request, 'user') and request.user is not None:
                # Log timestamp, user, request information
                logger.info(f"Timestamp: {datetime.now()}, User: {request.user}, Request path: {request.path}, Method: {request.method}")
            else:
                logger.info(f"Timestamp: {datetime.now()}, User: Not authenticated, Request path: {request.path}, Method: {request.method}")
        except AttributeError as e:
            logger.error(f"AttributeError in logging request: {e}")

        try:
            response = self.get_response(request)

            # Log timestamp, user, response information
            if hasattr(response, 'data') and 'result' in response.data:
                result = response.data['result']
                if result:
                    logger.info(f"Timestamp: {datetime.now()}, User: {request.user}, Response status: {response.status_code}, Success message: {response.data['message']}")
                else:
                    logger.error(f"Timestamp: {datetime.now()}, User: {request.user}, Response status: {response.status_code}, Error message: {response.data['message']}")
            else:
                logger.warning(f"Timestamp: {datetime.now()}, User: {request.user}, Response status: {response.status_code}, Unexpected response format")
        except Exception as e:
            logger.exception(f"Exception in processing request: {e}")
            raise

        return response
