from PySide2 import QtWidgets
from pyside2uic import compileUi
from xml.etree import ElementTree as ET
from io import StringIO


def loadUiType(uifile):
  xml = ET.parse(uifile)
  form_class = xml.find('class').text
  widget_class = xml.find('widget').get('class')
  with open(uifile) as ui:
    compiled = StringIO()
    compileUi(ui, compiled, indent=0)
    source = compiled.getvalue()
    ast = compile(source, '<string>', 'exec')
    scope = {}
    exec(ast, scope)
    form_class = scope['Ui_{}'.format(form_class)]
    widget_class = getattr(QtWidgets, widget_class)
  return form_class, widget_class
