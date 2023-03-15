#https://atufashireen.medium.com/creating-templates-with-jinja-in-python-3ff3b87d6740

from jinja2 import Environment, FileSystemLoader
from loguru import logger


FileName = "index.html"


def Generate(Context):
 logger.info(f"Generate {FileName}")
 Env = Environment(loader=FileSystemLoader("Template"))
 Template = Env.get_template("index.html")
 with open(FileName, mode="w", encoding="utf-8") as File:
  File.write(Template.render(Context))
