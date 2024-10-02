import json
from functools import wraps
import requests
import sys
from qtpy.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QTextEdit
from qtpy.QtCore import QRunnable, QThreadPool

API_HOST = "http://localhost:11434/api"


def run_off_main_thread(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		runner = QRunnable.create(lambda: func(*args, **kwargs))
		QThreadPool.globalInstance().start(runner)
	return wrapper


class Form(QDialog):
	def __init__(self, parent=None):
		super(Form, self).__init__(parent)
		self.setWindowTitle("Ollama API")

		self.layout = QVBoxLayout()
		self.prompt = QLineEdit()
		self.prompt.setPlaceholderText("Enter a prompt")
		self.submit = QPushButton("Submit")
		self.stream = QPushButton("Stream")
		self.clear = QPushButton("Clear")
		self.model_select = QComboBox()
		self.response = QTextEdit()

		self.layout.addWidget(self.prompt)
		self.layout.addWidget(self.model_select)
		self.layout.addWidget(self.submit)
		self.layout.addWidget(self.stream)
		self.layout.addWidget(self.clear)
		self.layout.addWidget(self.response)
		self.setLayout(self.layout)

		self.get_models()
		self.submit.clicked.connect(lambda: self.send_prompt())
		self.stream.clicked.connect(lambda: self.stream_response())
		self.clear.clicked.connect(lambda: self.clear_response())

	# https://github.com/ollama/ollama/blob/main/docs/api.md#list-local-models
	def get_models(self):
		response = requests.get(f"{API_HOST}/tags")
		print(response.json())
		for models in response.json().get("models"):
			self.model_select.addItem(models["model"])

	def clear_response(self):
		self.response.clear()

	@run_off_main_thread
	def send_prompt(self):
		prompt = self.prompt.text()
		model = self.model_select.currentText()
		response = requests.post(f"{API_HOST}/generate", json={
			"model": model,
			"prompt": prompt,
			"stream": False
		})
		print(response.json())
		self.response.insertPlainText(response.json().get("response"))

	@run_off_main_thread
	def stream_response(self):
		prompt = self.prompt.text()
		model = self.model_select.currentText()
		response = requests.post(f"{API_HOST}/generate", json={
			"model": model,
			"prompt": prompt,
			"stream": True
		}, stream=True)
		for line in response.iter_lines():
			if line:
				text = json.loads(line)["response"]
				print(text, end="")
				self.response.insertPlainText(text)



if __name__ == '__main__':
	app = QApplication(sys.argv)
	form = Form()
	form.show()
	sys.exit(app.exec())
