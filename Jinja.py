#https://atufashireen.medium.com/creating-templates-with-jinja-in-python-3ff3b87d6740

import os
from jinja2 import Environment, FileSystemLoader
from loguru import logger


Path = os.path.dirname(os.path.abspath(__file__))


def Generate(FileName, Context):
 logger.info(f"Generate {FileName}")
 Loader = FileSystemLoader("Template")
 Env = Environment(loader=Loader)
 Template = Env.get_template(FileName)
 Result = os.path.join(Path, "docs", FileName)
 with open(Result, mode="w", encoding="utf-8") as File:
  Render = Template.render(Context)
  File.write(Render)
