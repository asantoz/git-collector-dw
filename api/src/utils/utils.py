from src.exceptions.custom_exceptions import APIBadParameters


def try_parse_int(s, val=None):
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        return val


def validate_pagination(page, page_size):
    page = try_parse_int(page)
    page_size = try_parse_int(page_size)
    if(page is None):
        page = 1
    elif(page < 1):
        raise APIBadParameters("Page number should be greater than 1")

    if(page_size is None):
        page_size = 10
    elif(page_size > 100 or page_size < 1):
        raise APIBadParameters(
            "Page size should be greater than 1 and less than 100")
    return page, page_size
