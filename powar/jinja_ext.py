from jinja2 import nodes
from jinja2.ext import Extension

class ExternalExtension(Extension):
    tags = {"external"}

    def __init__(self, environment):
        super(ExternalExtension, self).__init__(environment)
        environment.extend(external_installs=[])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        filename = parser.parse_expression()
        body = parser.parse_statements(["name:endexternal"], drop_needle=True)
        return nodes.CallBlock(
            self.call_method("_render", [filename]), [], [], body
        ).set_lineno(lineno)

    def _render(self, install_filename: str, caller) -> str:
        self.environment.external_installs.append((install_filename, caller()))
        return ""
