import pyparsing as p 
import json

date = p.Combine(p.Word(p.nums, exact=2) + p.Literal("/") + p.Word(p.nums, exact=2) + p.Literal("/") + p.Word(p.nums, exact=4))

postcode_district = p.Combine(p.Word(p.alphas, min=1, max=2) + ((p.Word(p.nums, exact=1) + p.Word(p.alphas, exact=1)) | 
                                                                p.Word(p.nums, min=1, max=2))) + p.Suppress(p.White())

offence_code = p.Combine(p.Word(p.alphas, exact=2) + p.Word(p.nums, min=3)) + p.Suppress(p.White())

printed_by_line = p.Group(p.LineStart() + p.Literal("Printed By") + p.SkipTo(p.Literal("Page No.:")) + p.SkipTo(p.LineEnd())).setResultsName("printed_by")

first_case_line = p.Group(p.LineStart() + p.NotAny(p.White()) + p.Word(p.nums) + p.SkipTo(p.LineEnd())).setResultsName("first_case_line")

heading_block = p.Group(p.SkipTo(p.LineStart() + p.NotAny(p.White()) + p.Literal("Block:")) + p.SkipTo(p.LineEnd())).setResultsName("heading_block")

document = heading_block + p.OneOrMore(
  p.Group(p.SkipTo(first_case_line | printed_by_line)).setResultsName("main_body") + (first_case_line | (printed_by_line + p.Optional(heading_block) ))
)

def parse_court_docs(data):
    case_data = []

    all_results = document.parseString(data) 

    page_number = 1
    current_case_data = {}
    current_page_info = {}

    for item in all_results:
        if item.getName() == "heading_block":
            current_page_info = parse_heading_block(item)

        if item.getName() == "first_case_line":
            if current_case_data:
                current_case_data.update(parse_rest_case_data(current_case_data["rest_case_data"]))
                current_case_data.update(extra_info_from_case_data(current_case_data["rest_case_data"]))
                case_data.append(current_case_data)
            # new case
            current_case_data = {"rest_case_data": "", "page_number": page_number}
            current_case_data.update(parse_first_case_line(item))
            current_case_data.update(current_page_info)

        if item.getName() == "printed_by":
            page_number = page_number + 1

        if item.getName() == "main_body":
            if item[0]:
                current_case_data["rest_case_data"] += item[0]

    current_case_data.update(parse_rest_case_data(current_case_data["rest_case_data"]))
    current_case_data.update(extra_info_from_case_data(current_case_data["rest_case_data"]))

    case_data.append(current_case_data)
    return case_data


def parse_heading_block(heading_block):
    heading_block_string = " ".join(heading_block.asList())

    heading_block_detail = p.And([
        p.Suppress(p.SkipTo(date)),
        date("date"),
        p.SkipTo(p.Literal("LJA:")).setResultsName("court"),
        p.Suppress(p.Literal("LJA:")),
        p.SkipTo(p.Literal("CMU:")).setResultsName("LJA"),
        p.Suppress(p.Literal("CMU:")),
        p.SkipTo(p.Literal("Session:")).setResultsName("CMU"),
        p.Suppress(p.Literal("Session:")),
        p.SkipTo(p.Literal("Panel:")).setResultsName("Session"),
        p.Suppress(p.Literal("Panel:")),
        p.SkipTo(p.Literal("Courtroom:")).setResultsName("Panel"),
        p.Suppress(p.Literal("Courtroom:")),
        p.SkipTo(p.Literal("Block:")).setResultsName("Courtroom"),
        p.Suppress(p.Literal("Block:")),
        p.SkipTo(p.StringEnd()).setResultsName("Block")
    ])

    data = heading_block_detail.parseString(heading_block_string).asDict()

    return {key: value.strip() for key, value in data.items()}


def parse_first_case_line(first_case_line):
    data = {"case_order": first_case_line[0]}

    gender = p.Suppress(p.Literal("(")) + p.Word(p.alphas, exact=1).setResultsName("gender") + p.Suppress(p.Literal(")"))

    dob = p.Suppress(p.Literal("DOB:")) + date.setResultsName("dob") + p.Suppress(p.Literal("Age:")) + p.Word(p.nums).setResultsName("age")

    linked_case = p.Suppress(p.Literal("LINKED CASE"))
    provisional = p.Suppress(p.Literal("PROVISIONAL"))

    first_case_line_detail = p.And([
        p.SkipTo(p.White(" ", min=10) ^ gender).setResultsName("name"),
        p.Optional(gender),
        p.Optional(dob),
        p.Optional(linked_case),
        p.Optional(provisional),
        p.Word(p.nums),
    ])
    
    for key, value in first_case_line_detail.parseString(first_case_line[1]).asDict().items():
    	data[key] = value.strip()

    return data

def parse_rest_case_data(rest_case_data):
    data = {}
    listing = p.Suppress(p.Literal("(")) + p.Word(p.alphanums).setResultsName("listing") + p.Suppress(p.Literal("Listing)"))
    additional_info = p.And([
        p.SkipTo(p.Literal(": ")),
        p.Suppress(p.Literal(": ")),
        p.SkipTo(p.White(min=2) | p.StringEnd()),
    ])

    rest_case_data_detail = p.And([
        p.SkipTo(listing).setResultsName("address"), 
        listing,
        p.SkipTo(p.LineStart() + p.Word(p.nums)).setResultsName("additional_info"),
        p.SkipTo(p.StringEnd()).setResultsName("rest_case_data")
    ])


    for key, value in rest_case_data_detail.parseString(rest_case_data).asDict().items():
        if key == "address":
            data['address'] = value[0].strip()
        elif key == "additional_info":
            additional_info = p.ZeroOrMore(p.Group(additional_info)).parseString(value[0])
            data.update(dict(additional_info.asList()))
        else:
            data[key] = value.strip()
    return data

def extra_info_from_case_data(case_data):
    data = {}
    data['possible_postcode_districts'] = list(set(item[0][0] for item in postcode_district.scanString(case_data)))
    data['possible_offence_date'] = list(set(item[0][0] for item in date.scanString(case_data)))
    data['possible_offence_code'] = list(set(item[0][0] for item in offence_code.scanString(case_data)))
    return data


if __name__ == '__main__':
    # courts.txt comes from running
    # pdftotext -layout courts.pdf

    with open("courts_data/courts.txt") as doc:
        data = doc.read()
        parsed = parse_court_docs(data)

    safe_output = []

    # Remove juveniles before writing out
    for case in parsed:
        if 'age' in case.keys():
            if int(case['age']) >= 18:
                safe_output.append(case)
        elif 'LJA' != "North London Youth Court":
            safe_output.append(case)

    with open("courts_data/courts.json", "w+") as output:
        json.dump(safe_output, output, indent=4)


