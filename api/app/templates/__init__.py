from jinja2 import Environment, FileSystemLoader

prompt_templates = Environment(
    loader=FileSystemLoader("app/templates/prompts")
)
email_templates = Environment(
    loader=FileSystemLoader("app/templates/emails/build")
)

__all__ = ["prompt_templates", "email_templates"]
