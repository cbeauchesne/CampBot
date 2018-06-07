from .core import MarkdownProcessor, Converter
import re


class MarkdownCleaner(MarkdownProcessor):
    ready_for_production = True
    comment = "Clean markdown"

    def init_modifiers(self):
        self.modifiers = [
            Converter(pattern=r"\n{3,}",
                      repl=r"\n\n"),

            Converter(pattern=r"^\n*",
                      repl=r""),

            Converter(pattern=r"\n*$",
                      repl=r""),

            Converter(pattern=r"(^|\n)(#+) *",
                      repl=r"\1\2 "),
        ]


class OrthographicProcessor(MarkdownProcessor):
    def modify(self, markdown):
        placeholders = {}

        def protect(pattern, ph, markdown):

            def repl(match):
                markdown = match.group(0)

                if markdown not in placeholders:
                    placeholders[markdown] = ph.format(len(placeholders))

                return placeholders[markdown]

            return re.sub(pattern, repl, markdown)

        result = markdown

        STX = '\u0002'  # Use STX ("Start of text") for start-of-placeholder
        ETX = '\u0003'  # Use ETX ("End of text") for end-of-placeholder
        placeholder_pattern = STX + "ph{}ph" + ETX

        result = protect(r"https?://[^ )\n>]*", placeholder_pattern, result)
        result = protect(r"www\.[^ )\n>\]]*", placeholder_pattern, result)
        result = protect(r"\[\[[a-z]+/\d+/[/a-z\-#]+\|", "[[" + placeholder_pattern + "|", result)
        result = protect(r":\w+:", ":" + placeholder_pattern + ":", result)

        result = super().modify(result)

        for url, placeholder in placeholders.items():
            result = result.replace(placeholder, url)

        return result


class UpperFix(OrthographicProcessor):
    comment = "Upper case first letter"
    ready_for_production = True

    def init_modifiers(self):
        def upper(match):
            return match.group(0).upper()

        def ltag_converter(markdown):
            result = []

            cell_pattern = re.compile(r'(\| *[a-zéèà])(?![^|]*\]\])')

            is_ltag = False

            for line in markdown.split("\n"):

                if len(line) == 0:
                    is_ltag = False

                if line.startswith("L#") or line.startswith("R#"):
                    is_ltag = True

                if is_ltag:
                    result.append(cell_pattern.sub(upper, line))

                else:
                    result.append(line)

            return "\n".join(result)

        self.modifiers = [
            Converter(r"(^|\n)#+ *[a-zéèà]", upper),
            Converter(r"(^|\n\n)[a-zéèà]", upper),
            ltag_converter,
        ]


class MultiplicationSign(OrthographicProcessor):
    comment = "Multiplication sign"
    ready_for_production = True

    def init_modifiers(self):
        self.modifiers = [

            Converter(r"(\b\d)([*xX])(\d+) ?(m\b)",
                      r"\1×\3 \4")
        ]


class SpaceBetweenNumberAndUnit(OrthographicProcessor):
    lang = "fr"
    comment = "Espace entre chiffre et unité"
    ready_for_production = True

    def init_modifiers(self):
        self.modifiers = [
            Converter(r"(^|[| \n\(])(\d+)(m|km|h|mn|min|s)($|[ |,.?!:;\)\n])",
                      r"\1\2 \3\4"),

            Converter(r"(^|[| \n\(])(\d+)([\-xX])(\d+)(m|km|h|mn|min|s)($|[ |,.?!:;\)\n])",
                      r"\1\2\3\4 \5\6"),
        ]


class AutomaticReplacements(OrthographicProcessor):
    ready_for_production = True

    def __init__(self, lang, comment, replacements):
        self.replacements = replacements
        super().__init__()
        self.lang = lang
        self.comment = comment
        self.placeholders = None

    def init_modifiers(self):
        self.modifiers = []

        for old, new in self.replacements:
            self.modifiers.append(
                Converter(
                    r"\b" + old.strip() + r"\b",
                    new.strip()
                )
            )
