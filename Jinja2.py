import os

from loguru import logger
from jinja2 import Environment, FileSystemLoader


#https://atufashireen.medium.com/creating-templates-with-jinja-in-python-3ff3b87d6740
def Generate(List, Context):
 logger.info(f"Generate")
 Path = os.path.dirname(os.path.abspath(__file__))
 Loader = FileSystemLoader("Template")
 Env = Environment(loader=Loader)
 for Name in List:
  for Ext in [".html", ".csv"]:
   FileName = f"{Name}{Ext}"
   if os.path.isfile(os.path.join(Path, "Template", FileName)):
    Template = Env.get_template(FileName)
    Render = Template.render(Context)
    FullName = os.path.join(Path, "docs", FileName)
    with open(FullName, mode="w", encoding="utf-8") as File:
     File.write(Render)
