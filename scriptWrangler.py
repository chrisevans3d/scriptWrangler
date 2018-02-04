from PySide import QtCore, QtGui, QtUiTools

import syntax

#TODO:
# persistent scratch pads, saved on close, maybe autosave
# store latest sizes() on resize
# execute selected text only

def loadUiWidget(uifilename, parent=None):
	loader = QtUiTools.QUiLoader()
	uifile = QtCore.QFile(uifilename)
	uifile.open(QtCore.QFile.ReadOnly)
	ui = loader.load(uifile, parent)
	uifile.close()
	return ui

class OutputWrapper(QtCore.QObject):
	'''
	https://stackoverflow.com/questions/19855288/duplicate-stdout-stderr-in-qtextedit-widget
	'''
	outputWritten = QtCore.Signal(object, object)

	def __init__(self, parent, stdout=True):
		QtCore.QObject.__init__(self, parent)
		if stdout:
			self._stream = sys.stdout
			sys.stdout = self
		else:
			self._stream = sys.stderr
			sys.stderr = self
		self._stdout = stdout

	def write(self, text):
		self._stream.write(text)
		self.outputWritten.emit(text, self._stdout)

	def __getattr__(self, name):
		return getattr(self._stream, name)

	def __del__(self):
		try:
			if self._stdout:
				sys.stdout = self._stream
			else:
				sys.stderr = self._stream
		except AttributeError:
			pass

class ScriptWrangler(QtGui.QDialog):
	def __init__(self, parent=None):
		super(ScriptWrangler, self).__init__(parent)
		self.ui = loadUiWidget("C:\\Users\\chrise\\Dropbox\\python\\scriptWrangler\\scriptWrangler.ui")
		
		#connect the UI to code
		self.ui.execute_BTN.pressed.connect(self.execute_fn)
		self.ui.load_BTN.pressed.connect(self.load_fn)
		self.ui.tabs_WID.currentChanged.connect(self.tab_changed_fn)
		
		#stdout
		self._err_color = QtCore.Qt.red
		stdout = OutputWrapper(self, True)
		stdout.outputWritten.connect(self.handleOutput)
		stderr = OutputWrapper(self, False)
		stderr.outputWritten.connect(self.handleOutput)
		
		#syntax highlighting
		highlight = syntax.PythonHighlighter(self.ui.script_TEXT.document())
		
		#key binding
		QtGui.QShortcut(QtGui.QKeySequence("Alt+Return"), self.ui.tabs_WID, self.execute_fn, context=QtCore.Qt.WidgetShortcut)
		
		'''
		#have the terminal start closed
		self.sizes = self.ui.splitter.sizes()
		print self.sizes
		total_size = self.sizes[0] + self.sizes[1]
		self.ui.splitter.setSizes([300,300])
		'''
		
		self.ui.show()
	
	def handleOutput(self, text, stdout):
		color = self.ui.terminal.textColor()
		self.ui.terminal.setTextColor(color if stdout else self._err_color)
		self.ui.terminal.moveCursor(QtGui.QTextCursor.End)
		self.ui.terminal.insertPlainText(text)
		self.ui.terminal.setTextColor(color)
		
	def handleButton(self):
		if QtCore.QTime.currentTime().second() % 2:
			print('Printing to stdout...')
		else:
			sys.stderr.write('Printing to stderr...\n')
	
	def _mark_input_lines(self, lines, console = '>> '):
		marked_lines = None
		for line in lines.splitlines():
			if marked_lines == None:
				marked_lines = console + line + '\n'
			else:
				marked_lines += console + line + '\n'
		return marked_lines
	
	def create_new_tab(self, title, data=None):
		insertion_index = self.ui.tabs_WID.count() - 1
		
		#build new tab
		tab_wid = QtGui.QWidget()
		text_edit = QtGui.QPlainTextEdit
		
		#TODO: add data, add QPlainTextEdit
		# use this to create the first tab?
		
		self.ui.tabs_WID.insertTab(insertion_index, tab_wid, title)
		self.ui.tabs_WID.setCurrentIndex(insertion_index)
		


	## UI FUNCTIONS #############################################
	def execute_fn(self, debug=1):
		#TODO:  execute selected code
		input_block = self.ui.script_TEXT.toPlainText()
		
		if debug:
			print self._mark_input_lines(input_block)
		exec(input_block)
		
		'''
		#sizes not working, returns [0,0]
		print self.sizes
		#open terminal
		if self.ui.splitter.sizes()[1] == 0:
			print self.sizes
			self.ui.splitter.setSizes(self.sizes)
			self.ui.splitter.refresh()
		'''
		
	def load_fn(self):
		python_file = QtGui.QFileDialog.getOpenFileName(caption="Open Python Script", dir='C:\\\\', filter = "Python Files (*.py)")
		infile = open(python_file[0], 'r')
		
		#convert tabs to 4 spaces
		in_text = ''
		for line in infile.readlines():
			new_line = line.replace('\t', '    ')
			if in_text == '':
				in_text = new_line
			else:
				in_text += new_line
		
		self.ui.script_TEXT.setPlainText(in_text)
		infile.close()
		
	def tab_changed_fn(self, idx):
		#is the user clicking the '+' tab/button?
		if idx == self.ui.tabs_WID.count()-1:
			self.create_new_tab('ScratchPad')


if __name__ == "__main__":
	import sys
	app = QtGui.QApplication(sys.argv)
	main_window = ScriptWrangler()
	sys.exit(app.exec_())