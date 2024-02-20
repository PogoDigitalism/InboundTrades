def parse_query_params(url: str, params: dict[str, str | int | float]):
    for name, value in params.items():
        url = url.replace(f"${name}$", str(value))

    return url