HTML_TABLE = "table"
HTML_HEADING_ONE = "h1"
HTML_HEADING_TWO = "h2"
HTML_TR = "tr"
HTML_TD = "td"


def create_heading_one(heading: str) -> str:
    return f"<{HTML_HEADING_ONE}>{heading}</{HTML_HEADING_ONE}>"


def create_heading_two(heading: str) -> str:
    return f"<{HTML_HEADING_TWO}>{heading}</{HTML_HEADING_TWO}>"


def create_table(table_items: list[str]) -> str:
    table = [f"<{HTML_TABLE}>"]
    [table.append(f"<{HTML_TR}><{HTML_TD}>{item}</{HTML_TD}></{HTML_TR}>") for item in table_items]
    table.append(f"</{HTML_TABLE}>")

    return "".join(table)
