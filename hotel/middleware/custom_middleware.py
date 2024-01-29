import logging
from datetime import datetime
from watchtower import CloudWatchLogHandler
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

cloudwatch_handler = CloudWatchLogHandler(
    log_group='HouMuch',
    stream_name='HouMuchLogs',
    create_log_group=True,
    use_queues=False,
)
cloudwatch_handler.setLevel(logging.DEBUG)
cloudwatch_handler.setFormatter(formatter)
logger.addHandler(cloudwatch_handler)


class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            start_time = datetime.now()
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', 'unknown')
            if client_ip == 'unknown':
                client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            url = request.build_absolute_uri()
            request_body = request.body.decode('utf-8') if request.body else 'N/A'
            request_headers = dict(request.headers)

            # Store request and response information in separate dictionaries
            request_info = (
                f"Api call time: {start_time}\n"
                # f"{user_info}\n"
                f"Client IP: {client_ip}\n"
                # f"Request path: {request.path}\n"
                f"URL: {url}\n"
                f"Method: {request.method}\n"
                f"Headers: {json.dumps(request_headers, indent=2)}\n"
                f"Body: {request_body}"
            )

            response = self.get_response(request)

            end_time = datetime.now()
            execution_time = end_time - start_time

            if hasattr(response, 'data') and 'result' in response.data:
                response_data = json.dumps(response.data, indent=2)

                response_info = (
                    f"Api response time: {end_time}\n"
                    # f"{user_info}\n"
                    # f"Client IP: {client_ip}\n"
                    f"Response status: {response.status_code}\n"
                    f"Response data: {response_data}\n"
                    f"Execution time: {execution_time.total_seconds()} seconds"
                )

                # Log the combined information
                log_entry = (
                    f"Request Info:\n{request_info}\n"
                    f"Response Info:\n{response_info}"
                )

                # Log the combined information
                if 200 <= response.status_code < 300:
                    logger.info(log_entry)
                elif 300 <= response.status_code < 400:
                    logger.warning(log_entry)
                else:
                    logger.error(log_entry)

            else:
                warning_info = (
                    f"Timestamp: {end_time}\n"
                    f"Response status: {response.status_code}\n"
                    f"Unexpected response format\n"
                    f"Execution time: {execution_time.total_seconds()} seconds"
                )

                # Log the combined warning information
                log_entry = (
                    f"Request Info:\n{request_info}\n"
                    f"Warning Info:\n{warning_info}"
                )

                # Log the combined warning information
                if 200 <= response.status_code < 300:
                    logger.warning(log_entry)
                else:
                    logger.error(log_entry)

        except Exception as e:
            # Log as an error in case of an exception
            logger.error(f"Exception in processing request: {e}")
            raise

        return response
