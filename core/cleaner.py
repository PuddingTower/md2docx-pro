import os
import re
from typing import Dict, Tuple, Optional


class CodeProtector:
    """
    Protects inline code (`...`) and code blocks (```...```) from 
    unintended regex transformations during text cleanup.
    """
    def __init__(self):
        self.placeholders: Dict[str, str] = {}
        self.counter = 0

    def protect(self, text: str) -> str:
        """Extracts code blocks/inline code and replaces them with unique placeholders."""
        def replace_fenced(match):
            placeholder = f"___FENCED_CODE_BLOCK_{self.counter}___"
            self.placeholders[placeholder] = match.group(0)
            self.counter += 1
            return placeholder

        def replace_inline(match):
            placeholder = f"___INLINE_CODE_BLOCK_{self.counter}___"
            self.placeholders[placeholder] = match.group(0)
            self.counter += 1
            return placeholder

        # Match multiline code blocks (both backticks and tildes)
        text = re.sub(r'(?ms)^[ \t]*(`{3,}|~{3,})[^\n]*\n.*?\n[ \t]*\1[ \t]*$', replace_fenced, text)
        # Fallback for inline/non-standard fenced blocks
        text = re.sub(r'```[\s\S]*?```', replace_fenced, text)
        text = re.sub(r'`[^`\n]+`', replace_inline, text)
        return text

    def restore(self, text: str) -> str:
        """Restores original code blocks back into the text."""
        for placeholder, original in self.placeholders.items():
            text = text.replace(placeholder, original)
        return text


class MarkdownCleaner:
    """
    Handles global text normalization, unescaping, citation cleaning,
    table formatting fixes, and LaTeX formula standardization for Pandoc compatibility.
    """

    @staticmethod
    def global_text_clean(text: str) -> str:
        """
        Normalizes full-width digits/letters and invisible spaces without touching
        Chinese punctuation — NFKC would rewrite ，。：（） into ASCII and make
        mixed Chinese text look inconsistent.
        """
        if text.startswith('\ufeff'):
            text = text[1:]

        out = []
        for ch in text:
            cp = ord(ch)
            if 0xFF10 <= cp <= 0xFF19 or 0xFF21 <= cp <= 0xFF3A or 0xFF41 <= cp <= 0xFF5A:
                out.append(chr(cp - 0xFEE0))
            elif ch in ('\u00a0', '\u3000'):
                out.append(' ')
            elif ch == '\u200b':
                continue
            else:
                out.append(ch)
        return ''.join(out)

    @staticmethod
    def fix_dirty_code_fences(text: str) -> str:
        """
        Cleans web DOM class names and abnormal tags copied from web pages.
        e.g.: ```code-container formatted ng-tns-c754513404-19 -> ```text
        """
        def clean_fence_header(match):
            leading_ws = match.group(1)
            fence = match.group(2)
            info = match.group(3).strip()

            is_dirty_web_tag = bool(re.search(r'(code-container|ng-tns|formatted|no-decoration|highlight|copy-code)', info))
            
            if is_dirty_web_tag:
                return f"{leading_ws}{fence}text\n"
            
            if ' ' in info and not (info.startswith('{') and info.endswith('}')):
                first_token = info.split()[0]
                if re.match(r'^[a-zA-Z0-9_\-]+$', first_token):
                    return f"{leading_ws}{fence}{first_token}\n"
                return f"{leading_ws}{fence}text\n"
            
            return f"{leading_ws}{fence}{info}\n"

        return re.sub(r'(^|\n)([ \t]*)(`{3,}|~{3,})([^\n]*)\n', 
                      lambda m: clean_fence_header(re.match(r'(^|\n)([ \t]*)(`{3,}|~{3,})([^\n]*)\n', m.group(0))), 
                      text)

    @staticmethod
    def fix_markdown_structural_spacing(text: str) -> str:
        """
        Pandoc pipe_tables require empty line before tables and headings,
        otherwise tables or headings may be merged into paragraphs.
        """
        # 1. Ensure empty line before Markdown table
        text = re.sub(r'([^\n\s|].*?)\n(\|[^\n]+\|\n\|[\s:\-|]+\|)', r'\1\n\n\2', text)

        # 2. Ensure empty line before headings
        text = re.sub(r'([^\n\s].*?)\n(#{1,6}\s+)', r'\1\n\n\2', text)

        # 3. Ensure empty line before code blocks
        text = re.sub(r'([^\n\s].*?)\n([ \t]*`{3,})', r'\1\n\n\2', text)

        return text

    @staticmethod
    def clean_markdown_body_escapes(text: str) -> str:
        """Removes over-escaped Markdown syntax characters."""
        def de_escape(match):
            return match.group(1)

        pattern = re.compile(r'\\+([+\-=%\~#\*])')
        text = pattern.sub(de_escape, text)
        
        # Fix backslash space "\ " -> " " in Chinese context
        text = re.sub(r'(?<!\\)\\ (?!\\)', ' ', text)
        return text

    @staticmethod
    def clean_citation_noise(text: str) -> str:
        """Removes automated web capture timestamps and citation noise."""
        pattern = re.compile(r',\s*访问时间为\s*[\u4e00-\u9fa5]+\s+\d{1,2},\s+\d{4}')
        text = pattern.sub('', text)
        pattern_en = re.compile(r',\s*accessed\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}', re.IGNORECASE)
        return pattern_en.sub('', text)

    @staticmethod
    def clean_latex_syntax(text: str) -> str:
        """
        Standardizes LaTeX syntax for Pandoc OMML math conversion.
        """
        def math_replacer(match):
            content = match.group(0)
            
            # Subscript/Superscript double-escapes: C_{T\\_req} -> C_{T_req}
            content = content.replace(r'\\_', '_')
            content = content.replace(r'\\,', r'\,')
            
            content = content.replace(r'\_', '_')
            content = content.replace(r'\=', '=')
            content = content.replace(r'\<', '<')
            content = content.replace(r'\>', '>')
            content = content.replace(r'\-', '-')
            content = content.replace(r'\*', '*')
            
            content = content.replace(r'\(', '(').replace(r'\)', ')')
            content = content.replace(r'\[', '[').replace(r'\]', ']')
            
            # Multi-line break normalization: fix 3+ backslashes to \\
            content = re.sub(r'\\{3,}', r'\\\\', content)
            content = re.sub(r'\\\\([a-zA-Z]+)', r'\\\1', content)
            content = content.replace(r'\\{', r'\{').replace(r'\\}', r'\}')
            
            # Left/right delimiter cleanup
            content = content.replace(r'\left^', '^')
            content = content.replace(r'\right^', '^')
            content = re.sub(r'\\left(?=[^(){}\[\]|.\\])', '', content)
            content = re.sub(r'\\right(?=[^(){}\[\]|.\\])', '', content)

            # Auto-wrap multi-line equations in aligned environment
            if content.startswith('$$') and content.endswith('$$'):
                inner_content = content[2:-2].strip()
                if (r'\\' in inner_content or '\n' in inner_content) and not re.search(r'\\begin\{(aligned|align|equation|matrix|bmatrix|pmatrix|cases)\}', inner_content):
                    content = r'$$ \begin{aligned}' + inner_content + r'\end{aligned} $$'

            return content

        pattern = re.compile(r'(\$\$[\s\S]*?\$\$|\$(?!\s)[^\n$]*?\S\$|\$[^\n$]\$)')
        return pattern.sub(math_replacer, text)

    @staticmethod
    def extract_title_or_first_line(text: str, default_name: str = "未命名文档") -> str:
        """
        Extracts the first H1/H2 title or first non-empty line as candidate document name.
        Safe for Windows filenames.
        """
        for line in text.splitlines():
            line_s = line.strip()
            if not line_s:
                continue
            if line_s.startswith('#'):
                title = line_s.lstrip('#').strip()
                title = re.sub(r'[\\/*?:"<>|]', '_', title)
                if title:
                    return title[:60]
            elif len(line_s) > 2:
                title = re.sub(r'[\\/*?:"<>|]', '_', line_s)
                return title[:40]
        return default_name

    def process(self, text: str) -> str:
        """Runs the entire multi-stage cleaning pipeline safely in order."""
        s1 = self.global_text_clean(text)
        s2 = self.fix_dirty_code_fences(s1)
        s3 = self.fix_markdown_structural_spacing(s2)
        
        protector = CodeProtector()
        protected_text = protector.protect(s3)
        
        s4 = self.clean_markdown_body_escapes(protected_text)
        s5 = self.clean_citation_noise(s4)
        s6 = self.clean_latex_syntax(s5)
        
        final_text = protector.restore(s6)
        return final_text
