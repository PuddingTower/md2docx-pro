import os
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
import pypandoc

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace('w', W_NS)

# Bump when the generated reference documents change; stale caches rebuild themselves.
STYLE_VERSION = "2026.10.29-6"

# Content box of an A4 page with 2.2cm side margins (twips), used by templates and post-processing.
PAGE_W, PAGE_H = 11906, 16838
MARGIN_TB, MARGIN_LR = 1440, 1247
CONTENT_W = PAGE_W - 2 * MARGIN_LR

PPR_ORDER = [
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
    "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens",
    "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN",
    "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing",
    "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
    "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange",
]

RPR_ORDER = [
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
    "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden",
    "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect",
    "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout",
    "specVanish", "oMath",
]

TCPR_ORDER = [
    "cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap",
    "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark", "headers", "cellIns",
    "cellDel", "cellMerge", "tcPrChange",
]

_THEME_FONT_ATTRS = ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")
_THEME_COLOR_ATTRS = ("themeColor", "themeShade", "themeTint")


def qn(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _ensure_child(parent, tag: str, order):
    """Returns the child element, creating it at its schema-correct position."""
    existing = parent.find(qn(tag))
    if existing is not None:
        return existing
    child = ET.Element(qn(tag))
    idx = order.index(tag) if tag in order else len(order)
    pos = 0
    for i, sibling in enumerate(list(parent)):
        sib_tag = sibling.tag.split('}')[-1]
        if sib_tag in order and order.index(sib_tag) > idx:
            break
        pos = i + 1
    parent.insert(pos, child)
    return child


def _drop(parent, tag: str):
    node = parent.find(qn(tag))
    if node is not None:
        parent.remove(node)


def apply_run_style(rPr, latin: Optional[str] = None, ea: Optional[str] = None,
                    size: Optional[int] = None, color: Optional[str] = None,
                    bold: Optional[bool] = None, italic: Optional[bool] = None,
                    underline: Optional[bool] = None, fill: Optional[str] = None):
    if latin or ea:
        rFonts = _ensure_child(rPr, 'rFonts', RPR_ORDER)
        for attr in _THEME_FONT_ATTRS:
            rFonts.attrib.pop(qn(attr), None)
        if latin:
            rFonts.set(qn('ascii'), latin)
            rFonts.set(qn('hAnsi'), latin)
            rFonts.set(qn('cs'), latin)
        if ea:
            rFonts.set(qn('eastAsia'), ea)

    if bold is not None:
        if bold:
            _ensure_child(rPr, 'b', RPR_ORDER)
            _ensure_child(rPr, 'bCs', RPR_ORDER)
        else:
            _drop(rPr, 'b')
            _drop(rPr, 'bCs')

    if italic is not None:
        if italic:
            _ensure_child(rPr, 'i', RPR_ORDER)
            _ensure_child(rPr, 'iCs', RPR_ORDER)
        else:
            _drop(rPr, 'i')
            _drop(rPr, 'iCs')

    if size:
        _ensure_child(rPr, 'sz', RPR_ORDER).set(qn('val'), str(size))
        _ensure_child(rPr, 'szCs', RPR_ORDER).set(qn('val'), str(size))

    if color:
        node = _ensure_child(rPr, 'color', RPR_ORDER)
        for attr in _THEME_COLOR_ATTRS:
            node.attrib.pop(qn(attr), None)
        node.set(qn('val'), color)

    if underline is not None:
        if underline:
            _ensure_child(rPr, 'u', RPR_ORDER).set(qn('val'), 'single')
        else:
            _drop(rPr, 'u')

    if fill:
        shd = _ensure_child(rPr, 'shd', RPR_ORDER)
        shd.set(qn('val'), 'clear')
        shd.set(qn('color'), 'auto')
        shd.set(qn('fill'), fill)


def apply_paragraph_style(pPr, before: Optional[int] = None, after: Optional[int] = None,
                          line: Optional[int] = None, line_rule: str = 'auto',
                          left: Optional[int] = None, right: Optional[int] = None,
                          first_line: Optional[int] = None, first_line_chars: Optional[int] = None,
                          hanging: Optional[int] = None,
                          align: Optional[str] = None, keep_next: bool = False,
                          border: Optional[Tuple[str, int, str, int]] = None,
                          fill: Optional[str] = None, outline: Optional[int] = None,
                          widow_control: bool = True):
    if keep_next:
        _ensure_child(pPr, 'keepNext', PPR_ORDER)
        _ensure_child(pPr, 'keepLines', PPR_ORDER)
    if widow_control:
        _ensure_child(pPr, 'widowControl', PPR_ORDER)

    if border:
        side, sz, color, space = border
        pBdr = _ensure_child(pPr, 'pBdr', PPR_ORDER)
        for existing in list(pBdr):
            pBdr.remove(existing)
        node = ET.SubElement(pBdr, qn(side))
        node.set(qn('val'), 'single')
        node.set(qn('sz'), str(sz))
        node.set(qn('space'), str(space))
        node.set(qn('color'), color)

    if fill:
        shd = _ensure_child(pPr, 'shd', PPR_ORDER)
        shd.set(qn('val'), 'clear')
        shd.set(qn('color'), 'auto')
        shd.set(qn('fill'), fill)

    if before is not None or after is not None or line is not None:
        sp = _ensure_child(pPr, 'spacing', PPR_ORDER)
        if before is not None:
            sp.set(qn('before'), str(before))
            sp.set(qn('beforeAutospacing'), '0')
        if after is not None:
            sp.set(qn('after'), str(after))
            sp.set(qn('afterAutospacing'), '0')
        if line is not None:
            sp.set(qn('line'), str(line))
            sp.set(qn('lineRule'), line_rule)

    if left is not None or right is not None or first_line is not None \
            or first_line_chars is not None or hanging is not None:
        ind = _ensure_child(pPr, 'ind', PPR_ORDER)
        if left is not None:
            ind.set(qn('left'), str(left))
        if right is not None:
            ind.set(qn('right'), str(right))
        if hanging is not None:
            ind.attrib.pop(qn('firstLine'), None)
            ind.attrib.pop(qn('firstLineChars'), None)
            ind.set(qn('hanging'), str(hanging))
        elif first_line_chars is not None:
            ind.attrib.pop(qn('hanging'), None)
            ind.set(qn('firstLineChars'), str(first_line_chars))
            if first_line is not None:
                ind.set(qn('firstLine'), str(first_line))
        elif first_line is not None:
            ind.attrib.pop(qn('hanging'), None)
            ind.set(qn('firstLineChars'), '0')
            ind.set(qn('firstLine'), str(first_line))
        else:
            ind.attrib.pop(qn('hanging'), None)
            ind.set(qn('firstLineChars'), '0')
            ind.set(qn('firstLine'), '0')

    if align:
        _ensure_child(pPr, 'jc', PPR_ORDER).set(qn('val'), align)

    if outline is not None:
        _ensure_child(pPr, 'outlineLvl', PPR_ORDER).set(qn('val'), str(outline))


class TemplateManager:
    """
    Builds the three Word reference documents consumed by Pandoc.

    The presets deliberately differ in more than colour: font stacks, vertical rhythm,
    heading geometry and table grammar (executive banded tables vs. academic three-line
    tables vs. monochrome minimal rules) are all part of the design.
    """

    FONTS = {
        "modern":   {"latin": "Segoe UI",         "ea": "Microsoft YaHei", "heading_ea": "Microsoft YaHei", "mono": "Consolas"},
        "academic": {"latin": "Times New Roman",  "ea": "SimSun",          "heading_ea": "SimHei",          "mono": "Consolas"},
        "minimal":  {"latin": "Arial",            "ea": "Microsoft YaHei", "heading_ea": "Microsoft YaHei", "mono": "Consolas"},
    }

    BODY = {
        "modern":   dict(size=22, color="1F2937", line=360, before=0, after=120, align="left",  indent_chars=None, indent_twips=None),
        "academic": dict(size=24, color="000000", line=360, before=0, after=0,   align="both",  indent_chars=200,  indent_twips=480),
        "minimal":  dict(size=21, color="1F2937", line=336, before=0, after=160, align="left",  indent_chars=None, indent_twips=None),
    }

    HEADINGS = {
        "modern": {
            1: dict(size=34, color="0F172A", line=260, before=360, after=160, border=("bottom", 6, "E2E8F0", 10)),
            2: dict(size=26, color="0F172A", line=280, before=300, after=120),
            3: dict(size=23, color="334155", line=280, before=240, after=100),
            4: dict(size=22, color="475569", line=280, before=200, after=80),
            5: dict(size=21, color="475569", line=280, before=180, after=60),
            6: dict(size=21, color="64748B", line=280, before=180, after=60),
        },
        "academic": {
            1: dict(size=32, color="000000", line=300, before=320, after=180),
            2: dict(size=28, color="000000", line=300, before=280, after=140),
            3: dict(size=24, color="000000", line=300, before=240, after=120),
            4: dict(size=24, color="000000", line=300, before=200, after=100),
            5: dict(size=21, color="000000", line=300, before=180, after=80),
            6: dict(size=21, color="000000", line=300, before=180, after=80),
        },
        "minimal": {
            1: dict(size=32, color="111827", line=260, before=360, after=160, border=("bottom", 4, "D1D5DB", 10)),
            2: dict(size=24, color="111827", line=280, before=300, after=120),
            3: dict(size=22, color="374151", line=280, before=240, after=100),
            4: dict(size=21, color="4B5563", line=280, before=200, after=80),
            5: dict(size=21, color="4B5563", line=280, before=180, after=60),
            6: dict(size=21, color="6B7280", line=280, before=180, after=60),
        },
    }

    QUOTE = {
        "modern":   dict(size=21, color="475569", fill="F8FAFC", bar=("left", 18, "2563EB", 6), left=360, right=240),
        "academic": dict(size=21, color="333333", fill="F7F7F7", bar=("left", 12, "9CA3AF", 6), left=420, right=240),
        "minimal":  dict(size=20, color="4B5563", fill=None,     bar=("left", 18, "D1D5DB", 6), left=360, right=180),
    }

    CODE = {
        "modern":   dict(size=19, color="1F2328", fill="F6F8FA", bar=("left", 18, "E2E8F0", 8)),
        "academic": dict(size=19, color="1F2328", fill="F7F7F7", bar=("left", 12, "CCCCCC", 8)),
        "minimal":  dict(size=19, color="1F2328", fill="FAFAFA", bar=("left", 18, "E5E7EB", 8)),
    }

    INLINE_CODE = {
        "modern":   dict(color="0F172A", fill="F1F5F9"),
        "academic": dict(color="000000", fill="F2F2F2"),
        "minimal":  dict(color="111827", fill="F3F4F6"),
    }

    LINK_COLOR = {"modern": "2563EB", "academic": "1F4E79", "minimal": "111827"}

    CAPTION = {
        "modern":   dict(size=19, color="64748B", bold=False),
        "academic": dict(size=21, color="000000", bold=True),
        "minimal":  dict(size=18, color="6B7280", bold=False),
    }

    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            self.templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
        else:
            self.templates_dir = templates_dir
        os.makedirs(self.templates_dir, exist_ok=True)
        self.ensure_default_templates()

    def get_template_path(self, preset: str = "modern") -> str:
        preset = (preset or "modern").lower()
        if preset not in ("modern", "academic", "minimal"):
            preset = "modern"
        path = os.path.join(self.templates_dir, f"{preset}.docx")
        if not os.path.exists(path):
            self.build_preset(preset)
        return path

    def ensure_default_templates(self):
        version_file = os.path.join(self.templates_dir, ".style-version")
        current = ""
        if os.path.exists(version_file):
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    current = f.read().strip()
            except OSError:
                current = ""
        stale = current != STYLE_VERSION
        for preset in ("modern", "academic", "minimal"):
            path = os.path.join(self.templates_dir, f"{preset}.docx")
            if stale or not os.path.exists(path):
                self.build_preset(preset)
        if stale:
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(STYLE_VERSION)

    def _extract_base_reference_docx(self) -> str:
        """Extracts Pandoc's clean default reference.docx."""
        base_path = os.path.join(self.templates_dir, "pandoc_base.docx")
        if not os.path.exists(base_path) or os.path.getsize(base_path) < 1000:
            pandoc_bin = pypandoc.get_pandoc_path()
            with open(base_path, 'wb') as f:
                subprocess.run([pandoc_bin, '--print-default-data-file', 'reference.docx'], stdout=f, check=True)
        return base_path

    def build_preset(self, preset: str):
        """Constructs a tailored reference.docx with refined XML styles and page setup."""
        base_docx = self._extract_base_reference_docx()
        target_docx = os.path.join(self.templates_dir, f"{preset}.docx")
        temp_zip_out = target_docx + ".tmp"

        with zipfile.ZipFile(base_docx, 'r') as zin, \
                zipfile.ZipFile(temp_zip_out, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/styles.xml":
                    data = self._customize_styles_xml(data, preset)
                elif item.filename == "word/document.xml":
                    data = self._customize_page_setup(data)
                zout.writestr(item, data)

        if os.path.exists(target_docx):
            try:
                os.remove(target_docx)
            except OSError:
                pass
        os.rename(temp_zip_out, target_docx)

    @staticmethod
    def _customize_page_setup(xml_bytes: bytes) -> bytes:
        text = xml_bytes.decode("utf-8")
        sect = re.search(r"<w:sectPr(?:\s[^>]*)?>.*?</w:sectPr>", text, re.S)
        if not sect:
            return xml_bytes
        block = sect.group(0)
        block = re.sub(r"<w:pgSz[^>]*/>", "", block)
        block = re.sub(r"<w:pgMar[^>]*/>", "", block)
        page = (
            f'<w:pgSz w:w="{PAGE_W}" w:h="{PAGE_H}"/>'
            f'<w:pgMar w:top="{MARGIN_TB}" w:right="{MARGIN_LR}" w:bottom="{MARGIN_TB}" '
            f'w:left="{MARGIN_LR}" w:header="851" w:footer="992" w:gutter="0"/>'
        )
        footnote = re.search(r"</w:footnotePr>", block)
        if footnote:
            block = block[:footnote.end()] + page + block[footnote.end():]
        else:
            block = re.sub(r"(<w:sectPr(?:\s[^>]*)?>)", r"\1" + page, block, count=1)
        return (text[:sect.start()] + block + text[sect.end():]).encode("utf-8")

    def _customize_styles_xml(self, xml_bytes: bytes, preset: str) -> bytes:
        root = ET.fromstring(xml_bytes)
        styles = {s.get(qn('styleId')): s for s in root.findall(qn('style'))}
        fonts = self.FONTS[preset]
        body = self.BODY[preset]

        def style_rpr(style):
            return _ensure_child(style, 'rPr', ['name', 'aliases', 'basedOn', 'next', 'link',
                                                'autoRedefine', 'hidden', 'uiPriority',
                                                'semiHidden', 'unhideWhenUsed', 'qFormat',
                                                'locked', 'personal', 'personalCompose',
                                                'personalReply', 'rsid', 'pPr', 'rPr', 'tblPr',
                                                'trPr', 'tcPr', 'tblStylePr'])

        def style_ppr(style):
            return _ensure_child(style, 'pPr', ['name', 'aliases', 'basedOn', 'next', 'link',
                                                'autoRedefine', 'hidden', 'uiPriority',
                                                'semiHidden', 'unhideWhenUsed', 'qFormat',
                                                'locked', 'personal', 'personalCompose',
                                                'personalReply', 'rsid', 'pPr', 'rPr', 'tblPr',
                                                'trPr', 'tcPr', 'tblStylePr'])

        def base_run(style, size=None, color=None, bold=None, ea=None):
            apply_run_style(style_rpr(style), latin=fonts["latin"], ea=ea or fonts["ea"],
                            size=size, color=color, bold=bold)

        def body_like(style_id, first_paragraph=False):
            style = styles.get(style_id)
            if style is None:
                return
            base_run(style, size=body["size"], color=body["color"])
            indent_chars = body["indent_chars"]
            pPr = style_ppr(style)
            apply_paragraph_style(
                pPr,
                before=0 if first_paragraph else body["before"],
                after=body["after"],
                line=body["line"],
                align=body["align"],
                first_line=int(body["size"] * 10 * indent_chars / 100) if indent_chars else 0,
                first_line_chars=indent_chars,
                left=0,
            )

        # Defaults + core paragraph styles -------------------------------------------------
        default_rpr = root.find(f"{qn('docDefaults')}/{qn('rPrDefault')}/{qn('rPr')}")
        if default_rpr is None:
            doc_defaults = _ensure_child(root, 'docDefaults', ['docDefaults', 'latentStyles'])
            rpr_default = _ensure_child(doc_defaults, 'rPrDefault', ['rPrDefault', 'pPrDefault'])
            default_rpr = _ensure_child(rpr_default, 'rPr', RPR_ORDER)
        apply_run_style(default_rpr, latin=fonts["latin"], ea=fonts["ea"],
                        size=body["size"], color=body["color"])

        body_like("Normal", first_paragraph=True)
        body_like("BodyText")
        body_like("FirstParagraph", first_paragraph=True)
        body_like("Abstract")
        body_like("Bibliography")

        if "Bibliography" in styles:
            apply_paragraph_style(style_ppr(styles["Bibliography"]), left=480, hanging=480)

        compact = styles.get("Compact")
        if compact is not None:
            base_run(compact, size=body["size"], color=body["color"])
            apply_paragraph_style(style_ppr(compact), before=0, after=60,
                                  line=max(body["line"] - 60, 264), align="left",
                                  first_line=0)

        # Headings -------------------------------------------------------------------------
        for level, spec in self.HEADINGS[preset].items():
            style = styles.get(f"Heading{level}")
            if style is None:
                continue
            base_run(style, size=spec["size"], color=spec["color"], bold=True,
                     ea=fonts["heading_ea"])
            apply_run_style(style_rpr(style), italic=False)
            apply_paragraph_style(
                style_ppr(style),
                before=spec["before"], after=spec["after"], line=spec["line"],
                align="left", first_line=0,
                keep_next=True, border=spec.get("border"), outline=level - 1,
            )

        title = styles.get("Title")
        if title is not None:
            base_run(title, size=44, color=self.HEADINGS[preset][1]["color"], bold=True,
                     ea=fonts["heading_ea"])
            apply_paragraph_style(style_ppr(title), before=0, after=240, line=280,
                                  align="center", first_line=0, keep_next=True)

        subtitle = styles.get("Subtitle")
        if subtitle is not None:
            base_run(subtitle, size=26, color="64748B" if preset != "academic" else "333333")
            apply_paragraph_style(style_ppr(subtitle), before=0, after=240, line=280,
                                  align="center", first_line=0)

        # Block quotes ---------------------------------------------------------------------
        quote = self.QUOTE[preset]
        block = styles.get("BlockText")
        if block is not None:
            base_run(block, size=quote["size"], color=quote["color"])
            apply_paragraph_style(style_ppr(block), before=120, after=120, line=320,
                                  left=quote["left"], right=quote["right"], first_line=0,
                                  align="left", border=quote["bar"], fill=quote["fill"])

        # Code ----------------------------------------------------------------------------
        code = self.CODE[preset]
        source = styles.get("SourceCode")
        if source is None:
            source = ET.SubElement(root, qn('style'))
            source.set(qn('type'), 'paragraph')
            source.set(qn('styleId'), 'SourceCode')
            _ensure_child(source, 'name', ['name']).set(qn('val'), 'Source Code')
            _ensure_child(source, 'basedOn', ['name', 'basedOn']).set(qn('val'), 'Normal')
            styles["SourceCode"] = source
        base_run(source, size=code["size"], color=code["color"], ea=fonts["mono"])
        apply_paragraph_style(style_ppr(source), before=120, after=120, line=240,
                              left=0, right=0, first_line=0, align="left",
                              border=code["bar"], fill=code["fill"])
        _ensure_child(style_ppr(source), 'keepLines', PPR_ORDER)

        inline = self.INLINE_CODE[preset]
        verbatim = styles.get("VerbatimChar")
        if verbatim is not None:
            base_run(verbatim, size=code["size"] - 1, color=inline["color"], ea=fonts["mono"])
            apply_run_style(style_rpr(verbatim), fill=inline["fill"])

        # Links and captions ----------------------------------------------------------------
        link = styles.get("Hyperlink")
        if link is not None:
            base_run(link)
            apply_run_style(style_rpr(link), color=self.LINK_COLOR[preset], underline=True)

        cap = self.CAPTION[preset]
        for cap_id in ("Caption", "TableCaption", "ImageCaption"):
            style = styles.get(cap_id)
            if style is None:
                continue
            base_run(style, size=cap["size"], color=cap["color"], bold=cap["bold"])
            before, after = (200, 60) if cap_id == "TableCaption" else (60, 160)
            apply_paragraph_style(style_ppr(style), before=before, after=after, line=280,
                                  align="center", first_line=0, keep_next=(cap_id == "TableCaption"))
            apply_run_style(style_rpr(style), italic=False)

        # Table default: no borders, comfortable cell margins --------------------------------
        table = styles.get("Table")
        if table is not None:
            _drop(table, 'tblPr')
            tblPr = _ensure_child(table, 'tblPr', ['name', 'aliases', 'basedOn', 'next', 'link',
                                                   'autoRedefine', 'hidden', 'uiPriority',
                                                   'semiHidden', 'unhideWhenUsed', 'qFormat',
                                                   'locked', 'personal', 'personalCompose',
                                                   'personalReply', 'rsid', 'pPr', 'rPr', 'tblPr',
                                                   'trPr', 'tcPr', 'tblStylePr'])
            borders = ET.SubElement(tblPr, qn('tblBorders'))
            for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
                node = ET.SubElement(borders, qn(side))
                node.set(qn('val'), 'none')
                node.set(qn('sz'), '0')
                node.set(qn('space'), '0')
                node.set(qn('color'), 'auto')
            margins = ET.SubElement(tblPr, qn('tblCellMar'))
            for side, val in (("top", 70), ("left", 110), ("bottom", 70), ("right", 110)):
                node = ET.SubElement(margins, qn(side))
                node.set(qn('w'), str(val))
                node.set(qn('type'), 'dxa')

        # Belt and braces: no theme colour / theme font may leak past the presets ------------
        for rFonts in root.iter(qn('rFonts')):
            for attr in _THEME_FONT_ATTRS:
                rFonts.attrib.pop(qn(attr), None)
        for color in root.iter(qn('color')):
            for attr in _THEME_COLOR_ATTRS:
                color.attrib.pop(qn(attr), None)

        return ET.tostring(root, encoding='utf-8')
