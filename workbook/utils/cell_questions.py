from workbook.utils.questions import Question, publish_display_data

class CellQuestion(Question):

    shell = get_ipython()  # this class is defined by running through ipython...
    def __init__(self, cell_input):
        self.cell_input = cell_input
        
    def publish(self):
        self.shell.run_cell(self.cell_input)
        publish_display_data('CellQuestion', {'text/html':'I did it'})

    
