HTML_TABLE = "table"
HTML_HEADING_ONE = "h1"
HTML_HEADING_TWO = "h2"
HTML_TR = "tr"
HTML_TD = "td"


def create_heading_one(heading: str) -> str:
    return f"<{HTML_HEADING_ONE}>{heading}</{HTML_HEADING_ONE}>"


def create_heading_two(heading: str) -> str:
    return f"<{HTML_HEADING_TWO}>{heading}</{HTML_HEADING_TWO}>"


def create_link(link: str, text: str) -> str:
    return f'<a href="{link}">{text}</a>'


def create_paragraph(text: str) -> str:
    return f"<p>{text}</p>"


def create_pre(text: str) -> str:
    return f"<pre>{text}</pre>"


def create_table(table_header: list[str], table_items: list[tuple]) -> str:
    table = [f"<{HTML_TABLE}>", f"<{HTML_TR}>"]

    for th in table_header:
        table.append(f"<{HTML_TD}>{th}</{HTML_TD}>")
    table.append(f"</{HTML_TR}>")

    for ti in table_items:
        table.append(f"<{HTML_TR}>")
        for item in ti:
            table.append(f"<{HTML_TD}>{item}</{HTML_TD}>")
        table.append(f"</{HTML_TR}>")
    table.append(f"</{HTML_TABLE}>")

    return "".join(table)
