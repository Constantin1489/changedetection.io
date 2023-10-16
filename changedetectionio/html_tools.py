
from bs4 import BeautifulSoup
from inscriptis import get_text
from inscriptis.model.config import ParserConfig
from jsonpath_ng.ext import parse
from typing import List
import json
import re
from lxml import etree, html
import sys

# HTML added to be sure each result matching a filter (.example) gets converted to a new line by Inscriptis
TEXT_FILTER_LIST_LINE_SUFFIX = "<br>"

PERL_STYLE_REGEX = r'^/(.*?)/([a-z]*)?$'
# 'price' , 'lowPrice', 'highPrice' are usually under here
# All of those may or may not appear on different websites - I didnt find a way todo case-insensitive searching here
LD_JSON_PRODUCT_OFFER_SELECTORS = ["json:$..offers", "json:$..Offers"]

class JSONNotFound(ValueError):
    def __init__(self, msg):
        ValueError.__init__(self, msg)


# Doesn't look like python supports forward slash auto enclosure in re.findall
# So convert it to inline flag "(?i)foobar" type configuration
def perl_style_slash_enclosed_regex_to_options(regex):

    res = re.search(PERL_STYLE_REGEX, regex, re.IGNORECASE)

    if res:
        flags = res.group(2) if res.group(2) else 'i'
        regex = f"(?{flags}){res.group(1)}"
    else:
        # Fall back to just ignorecase as an option
        regex = f"(?i){regex}"

    return regex

# Given a CSS Rule, and a blob of HTML, return the blob of HTML that matches
def include_filters(include_filters, html_content, append_pretty_line_formatting=False):
    soup = BeautifulSoup(html_content, "html.parser")
    html_block = ""
    r = soup.select(include_filters, separator="")

    for element in r:
        # When there's more than 1 match, then add the suffix to separate each line
        # And where the matched result doesn't include something that will cause Inscriptis to add a newline
        # (This way each 'match' reliably has a new-line in the diff)
        # Divs are converted to 4 whitespaces by inscriptis
        if append_pretty_line_formatting and len(html_block) and not element.name in (['br', 'hr', 'div', 'p']):
            html_block += TEXT_FILTER_LIST_LINE_SUFFIX

        html_block += str(element)

    return html_block

def subtractive_css_selector(css_selector, html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for item in soup.select(css_selector):
        item.decompose()
    return str(soup)


def element_removal(selectors: List[str], html_content):
    """Joins individual filters into one css filter."""
    selector = ",".join(selectors)
    return subtractive_css_selector(selector, html_content)


def element_path_tostring(obj):
    import elementpath
    from decimal import Decimal
    import math

    if obj is None:
        return ''
    elif isinstance(obj, elementpath.XPathNode):
        return obj.string_value
    elif isinstance(obj, bool):
        return 'true' if obj else 'false'
    elif isinstance(obj, Decimal):
        value = format(obj, 'f')
        if '.' in value:
            return value.rstrip('0').rstrip('.')
        return value

    elif isinstance(obj, float):
        if math.isnan(obj):
            return 'NaN'
        elif math.isinf(obj):
            return str(obj).upper()

        value = str(obj)
        if '.' in value:
            value = value.rstrip('0').rstrip('.')
        if '+' in value:
            value = value.replace('+', '')
        if 'e' in value:
            return value.upper()
        return value

#    elif isinstance(obj, elementpath.XPathFunction):
#        if self.symbol in ('concat', '||'):
#            raise self.error('FOTY0013', f"an argument is a function")
#        else:
#            raise self.error('FOTY0014', f"{obj.label!r} has no string value")

    return str(obj)

# Return str Utf-8 of matched rules
def xpath_filter(xpath_filter, html_content, append_pretty_line_formatting=False):
    from lxml import etree, html
    import elementpath
    # xpath 2.0-3.1
    from elementpath.xpath3 import XPath3Parser

    tree = etree.HTML(bytes(html_content, encoding='utf-8'))
    #tree = html.fromstring(bytes(html_content, encoding='utf-8'))
    html_block = ""

    r =  elementpath.select(tree, xpath_filter.strip(), namespaces={'re': 'http://exslt.org/regular-expressions'}, parser=XPath3Parser)
    #@note: //title/text() wont work where <title>CDATA..

    # Because of elementpath lib.
    # e.g. string-join(//*[contains(@class, 'sametext')]|//*[matches(@class, 'changetext')], ', ')
    # e.g. r='Some text thats the same, Some new text' type(r)=<class 'str'>
    # e.g. count(//*[contains(@class, 'sametext')])
    # e.g. r=1 type(r)=<class 'int'>
    if type(r) != list:
        r = [r]

    for element in r:
        # When there's more than 1 match, then add the suffix to separate each line
        # And where the matched result doesn't include something that will cause Inscriptis to add a newline
        # (This way each 'match' reliably has a new-line in the diff)
        # Divs are converted to 4 whitespaces by inscriptis
        print(f"ln: 136 - {type(element)=}  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
        if type(element) == str:
            html_block += element
        if append_pretty_line_formatting and len(html_block) and (not hasattr( element, 'tag' ) or not element.tag in (['br', 'hr', 'div', 'p'])):
            html_block += TEXT_FILTER_LIST_LINE_SUFFIX
        # https://lxml.de/api/lxml.etree-module.html#tostring
        # https://lxml.de/api/lxml.etree._Element-class.html
        # https://lxml.de/api/lxml.etree._ElementTree-class.html
        elif issubclass(type(element),etree._Element) or issubclass(type(element), etree._ElementTree):
            print(f"ln: 136 - {type(element)=}  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
            print(f"ln: 136 - {dir(element)=}  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
            html_block += etree.tostring(element, pretty_print=True).decode('utf-8')
            #html_block += element_path_tostring(element)
        else:
            html_block += element_path_tostring(element)
#
#
#
#
#        if type(element) == etree._ElementStringResult:
#            print(f"ln: 152 - Note  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
#            html_block += str(element)
#        elif type(element) == etree._ElementUnicodeResult:
#            print(f"ln: 155 - Note  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
#            html_block += str(element)
#        # Because of elementpath lib.
#        # e.g. element='texts' type(element)=<class 'str'>
#        # e.g. //*[contains(@id,'post')]/div/div[2]/header/h2/a/text() | //*[contains(@id,'post')]/div/div[2]/header/h2/a/@href
#        elif type(element) == str:
#            print(f"ln: 161 - Note  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
#            html_block += element
#        # Because of elementpath lib.
#        # e.g. element=7 type(element)=<class 'int'>
#        # e.g. xpath://div/table/tbody/tr[*]/count(td)
#        elif type(element) == int:
#            print(f"ln: 167 - Note  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
#            html_block += str(element)
#        # e.g. element=<Element a at 0x7fcb0038c0e0> type(element)=<class 'lxml.html.HtmlElement'>
#        # e.g. //*[@id="container"]/section[1]/article[2]/div[2]/table/tbody/tr[*]/td[2]/a[1]
#        else:
#            print(f"ln: 172 - Note  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
#            print(f"ln: 136 - {type(element)=}  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
#            print(f"ln: 136 - {dir(element)=}  /mnt/finalresort/shelf-production/kvm/scripts/git_worktree_changedetection/changedetection.io/changedetectionio/html_tools.py ", file=sys.stderr)
#            html_block += etree.tostring(element, pretty_print=True).decode('utf-8')

    return html_block


# Extract/find element
def extract_element(find='title', html_content=''):

    #Re #106, be sure to handle when its not found
    element_text = None

    soup = BeautifulSoup(html_content, 'html.parser')
    result = soup.find(find)
    if result and result.string:
        element_text = result.string.strip()

    return element_text

#
def _parse_json(json_data, json_filter):
    if 'json:' in json_filter:
        jsonpath_expression = parse(json_filter.replace('json:', ''))
        match = jsonpath_expression.find(json_data)
        return _get_stripped_text_from_json_match(match)

    if 'jq:' in json_filter:

        try:
            import jq
        except ModuleNotFoundError:
            # `jq` requires full compilation in windows and so isn't generally available
            raise Exception("jq not support not found")

        jq_expression = jq.compile(json_filter.replace('jq:', ''))
        match = jq_expression.input(json_data).all()

        return _get_stripped_text_from_json_match(match)

def _get_stripped_text_from_json_match(match):
    s = []
    # More than one result, we will return it as a JSON list.
    if len(match) > 1:
        for i in match:
            s.append(i.value if hasattr(i, 'value') else i)

    # Single value, use just the value, as it could be later used in a token in notifications.
    if len(match) == 1:
        s = match[0].value if hasattr(match[0], 'value') else match[0]

    # Re #257 - Better handling where it does not exist, in the case the original 's' value was False..
    if not match:
        # Re 265 - Just return an empty string when filter not found
        return ''

    # Ticket #462 - allow the original encoding through, usually it's UTF-8 or similar
    stripped_text_from_html = json.dumps(s, indent=4, ensure_ascii=False)

    return stripped_text_from_html

# content - json
# json_filter - ie json:$..price
# ensure_is_ldjson_info_type - str "product", optional, "@type == product" (I dont know how to do that as a json selector)
def extract_json_as_string(content, json_filter, ensure_is_ldjson_info_type=None):
    stripped_text_from_html = False

    # Try to parse/filter out the JSON, if we get some parser error, then maybe it's embedded within HTML tags
    try:
        stripped_text_from_html = _parse_json(json.loads(content), json_filter)
    except json.JSONDecodeError:

        # Foreach <script json></script> blob.. just return the first that matches json_filter
        # As a last resort, try to parse the whole <body>
        soup = BeautifulSoup(content, 'html.parser')

        if ensure_is_ldjson_info_type:
            bs_result = soup.findAll('script', {"type": "application/ld+json"})
        else:
            bs_result = soup.findAll('script')
        bs_result += soup.findAll('body')

        bs_jsons = []
        for result in bs_result:
            # Skip empty tags, and things that dont even look like JSON
            if not result.text or '{' not in result.text:
                continue
            try:
                json_data = json.loads(result.text)
                bs_jsons.append(json_data)
            except json.JSONDecodeError:
                # Skip objects which cannot be parsed
                continue

        if not bs_jsons:
            raise JSONNotFound("No parsable JSON found in this document")
        
        for json_data in bs_jsons:
            stripped_text_from_html = _parse_json(json_data, json_filter)

            if ensure_is_ldjson_info_type:
                # Could sometimes be list, string or something else random
                if isinstance(json_data, dict):
                    # If it has LD JSON 'key' @type, and @type is 'product', and something was found for the search
                    # (Some sites have multiple of the same ld+json @type='product', but some have the review part, some have the 'price' part)
                    # @type could also be a list (Product, SubType)
                    # LD_JSON auto-extract also requires some content PLUS the ldjson to be present
                    # 1833 - could be either str or dict, should not be anything else
                    if json_data.get('@type') and stripped_text_from_html:
                        try:
                            if json_data.get('@type') == str or json_data.get('@type') == dict:
                                types = [json_data.get('@type')] if isinstance(json_data.get('@type'), str) else json_data.get('@type')
                                if ensure_is_ldjson_info_type.lower() in [x.lower().strip() for x in types]:
                                    break
                        except:
                            continue

            elif stripped_text_from_html:
                break

    if not stripped_text_from_html:
        # Re 265 - Just return an empty string when filter not found
        return ''

    return stripped_text_from_html

# Mode     - "content" return the content without the matches (default)
#          - "line numbers" return a list of line numbers that match (int list)
#
# wordlist - list of regex's (str) or words (str)
def strip_ignore_text(content, wordlist, mode="content"):
    i = 0
    output = []
    ignore_text = []
    ignore_regex = []
    ignored_line_numbers = []

    for k in wordlist:
        # Is it a regex?
        res = re.search(PERL_STYLE_REGEX, k, re.IGNORECASE)
        if res:
            ignore_regex.append(re.compile(perl_style_slash_enclosed_regex_to_options(k)))
        else:
            ignore_text.append(k.strip())

    for line in content.splitlines():
        i += 1
        # Always ignore blank lines in this mode. (when this function gets called)
        got_match = False
        if len(line.strip()):
            for l in ignore_text:
                if l.lower() in line.lower():
                    got_match = True

            if not got_match:
                for r in ignore_regex:
                    if r.search(line):
                        got_match = True

            if not got_match:
                # Not ignored
                output.append(line.encode('utf8'))
            else:
                ignored_line_numbers.append(i)


    # Used for finding out what to highlight
    if mode == "line numbers":
        return ignored_line_numbers

    return "\n".encode('utf8').join(output)


def html_to_text(html_content: str, render_anchor_tag_content=False) -> str:
    """Converts html string to a string with just the text. If ignoring
    rendering anchor tag content is enable, anchor tag content are also
    included in the text

    :param html_content: string with html content
    :param render_anchor_tag_content: boolean flag indicating whether to extract
    hyperlinks (the anchor tag content) together with text. This refers to the
    'href' inside 'a' tags.
    Anchor tag content is rendered in the following manner:
    '[ text ](anchor tag content)'
    :return: extracted text from the HTML
    """
    #  if anchor tag content flag is set to True define a config for
    #  extracting this content
    if render_anchor_tag_content:

        parser_config = ParserConfig(
            annotation_rules={"a": ["hyperlink"]}, display_links=True
        )

    # otherwise set config to None
    else:
        parser_config = None

    # get text and annotations via inscriptis
    text_content = get_text(html_content, config=parser_config)

    return text_content


# Does LD+JSON exist with a @type=='product' and a .price set anywhere?
def has_ldjson_product_info(content):
    pricing_data = ''

    try:
        if not 'application/ld+json' in content:
            return False

        for filter in LD_JSON_PRODUCT_OFFER_SELECTORS:
            pricing_data += extract_json_as_string(content=content,
                                                  json_filter=filter,
                                                  ensure_is_ldjson_info_type="product")

    except Exception as e:
        # Totally fine
        return False
    x=bool(pricing_data)
    return x


def workarounds_for_obfuscations(content):
    """
    Some sites are using sneaky tactics to make prices and other information un-renderable by Inscriptis
    This could go into its own Pip package in the future, for faster updates
    """

    # HomeDepot.com style <span>$<!-- -->90<!-- -->.<!-- -->74</span>
    # https://github.com/weblyzard/inscriptis/issues/45
    if not content:
        return content

    content = re.sub('<!--\s+-->', '', content)

    return content


def get_triggered_text(content, trigger_text):
    triggered_text = []
    result = strip_ignore_text(content=content,
                               wordlist=trigger_text,
                               mode="line numbers")

    i = 1
    for p in content.splitlines():
        if i in result:
            triggered_text.append(p)
        i += 1

    return triggered_text
