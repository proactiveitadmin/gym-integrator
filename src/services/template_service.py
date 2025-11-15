from ..domain.templates import render_template
class TemplateService:
    def render(self, template: str, context: dict):
        return render_template(template, context)
