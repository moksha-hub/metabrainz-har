import json
from urllib.parse import urlparse
from integuru.models.request import Request
from typing import Tuple, Dict, Optional, Any, List

METABRAINZ_DOMAINS = (
    "musicbrainz.org",
    "bookbrainz.org",
    "metabrainz.org",
    "listenbrainz.org",
    "coverartarchive.org",
    "acousticbrainz.org",
)


def is_metabrainz_url(url: str) -> bool:
    """Check if a URL belongs to the MetaBrainz ecosystem."""
    parsed_url = urlparse(url)
    return any(domain in parsed_url.netloc for domain in METABRAINZ_DOMAINS)


def format_request(har_request: Dict[str, Any]) -> Request:
    """
    Formats a HAR request into a Request object.
    """
    method = har_request.get("method", "GET")
    url = har_request.get("url", "")

    headers = {
        header.get("name", ""): header.get("value", "")
        for header in har_request.get("headers", [])
    }

    query_params_list = har_request.get("queryString", [])
    query_params = {
        param["name"]: param["value"] for param in query_params_list
    } if query_params_list else None

    post_data = har_request.get("postData", {})
    body = post_data.get("text") if post_data else None

    if body:
        headers_lower = {k.lower(): v for k, v in headers.items()}
        content_type = headers_lower.get('content-type')
        if content_type and 'application/json' in content_type.lower():
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                pass  # Keep body as is if not valid JSON

    return Request(
        method=method,
        url=url,
        headers=headers, 
        query_params=query_params,
        body=body
    )


def format_response(har_response: Dict[str, Any]) -> Dict[str, str]:
    """
    Extracts and returns the content text and content type from a HAR response.
    """
    content = har_response.get("content", {})
    return {
        "text": content.get("text", ""),
        "type": content.get("mimeType", "")
    }


def parse_har_file(har_file_path: str) -> Dict[Request, Dict[str, str]]:
    """
    Parses the HAR file and returns a dictionary mapping Request objects to response dictionaries,
    filtering only MetaBrainz-related data.
    """
    req_res_dict = {}

    with open(har_file_path, 'r', encoding='utf-8') as file:
        har_data = json.load(file)

    entries = har_data.get("log", {}).get("entries", [])

    for entry in entries:
        request_data = entry.get("request", {})
        response_data = entry.get("response", {})
        url = request_data.get("url", "")

        if is_metabrainz_url(url):
            formatted_request = format_request(request_data)
            response_dict = format_response(response_data)

            req_res_dict[formatted_request] = response_dict

    return req_res_dict


def get_metabrainz_urls(har_file_path: str) -> List[Tuple[str, str, str, str]]:
    """
    Extracts and returns a list of tuples containing method, URL, response format, and response preview
    from a HAR file, only for MetaBrainz endpoints.
    """
    urls_with_details = []

    with open(har_file_path, "r", encoding="utf-8") as file:
        har_data = json.load(file)

    entries = har_data.get("log", {}).get("entries", [])   
    for entry in entries:
        request = entry.get("request", {})
        response = entry.get("response", {})
        url = request.get("url")
        method = request.get("method", "GET")  # Default to 'GET' if method is missing
        response_format = response.get("content", {}).get("mimeType", "")
        response_text = response.get("content", {}).get("text", "")
        response_preview = response_text[:30] if response_text else ""

        if url and is_metabrainz_url(url):
            urls_with_details.append((method, url, response_format, response_preview))

    return urls_with_details
