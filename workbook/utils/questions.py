import numpy as np
from IPython.core.displaypub import publish_display_data
import json

class HomeworkCounter(object):

    def __init__(self):
        self.question_number = 0

    def next(self):
        self.question_number += 1
        publish_display_data("HomeworkBuilder", {'text/html':"<h2>Question %d</h2>" % self.question_number})
        publish_workbook_metadata({'worksheet':self.question_number})


def publish_workbook_metadata(metadata):
    publish_display_data("HomeworkBuilder", 
                         {"application/json":{"workbook_metadata":
                                                  metadata}})


class Question(object):

    def publish(self, return_data=False, display=True):
        raise NotImplementedError

    @property
    def constructor_info(self):
        return None

    def set_answer(self):
        raise NotImplementedError

    def get_answer(self):
        raise NotImplementedError

    answer = property(get_answer, set_answer)

    def check_answer(self, output, answer):
        raise NotImplementedError

class Generator(Question):
    pass

class MultipleChoice(object):

    checkable = True

    def __init__(self, identifier, question_text, choices, correct_answer,
                 assignment='assignment1', selected=None):

        if correct_answer not in list(choices):
            raise ValueError('the correct answer should be one of the choices! %s' % `(correct_answer, choices)`)
        if selected and selected not in list(choices):
            raise ValueError('selected answer should be one of the choices! %s' % `(selected, choices)`)

        self.choices = choices
        self.selected = selected
        self.question_text = question_text
        self.correct_answer = correct_answer
        # assignment should be removed
        self.assignment = assignment
        self.identifier = identifier

    @property
    def constructor_info(self):
        args = [self.identifier, self.question_text, self.choices, self.correct_answer]
        kw = {'assignment':self.assignment,
              'selected':self.selected}
        return ('multiple_choice', args, kw)

    def publish(self, return_data=False, display=True):

        latex_data = {'text/latex':self.question_text}

        d = {'identifier': self.identifier,
             'url': self.assignment}

        buttons = []
        for choice in self.choices:
            d['value'] = choice
            if choice == self.selected and self.selected:
                buttons.append("""<p><input type="radio" name=%(identifier)s value="%(value)s" id="%(value)s" checked="checked"> %(value)s</p>""" % d)
            else:
                buttons.append("""<p><input type="radio" name=%(identifier)s value="%(value)s" id="%(value)s"> %(value)s</p>""" % d)
        radio_code = ('<form name="%(identifier)s" method="post" >\n' % d) + '\n'.join(buttons) + '</form>\n'

        html_data = {'text/html': radio_code}
        json_data = {'application/json': {'identifier':self.identifier,
                                          'constructor_info':self.constructor_info}}

        if display:
            # this update puts the question identifier info in this output

            latex_data.update(json_data)
            publish_display_data("HomeworkBuilder", latex_data)

            html_data.update(json_data)
            publish_display_data("HomeworkBuilder", html_data)

        if return_data:
            data = {}
            for d in [latex_data, html_data, json_data]:
                data.update(d)
            return data

    # def check_answer(self, output, answer):
    #     self.answer = answer
    #     data = self.publish(return_data=True, display=False)
    #     if self.answer == self.correct_answer:
    #         if "html" in output.keys():
    #             output.html = data['text/html'].split('\n')
    #             output.html.append('\n<p><h2>Good job!</h2></p>\n')
    #     elif self.answer:
    #         if "html" in output.keys():
    #             output.html = data['text/html'].split('\n')
    #             output.html.append('\n<p><h2>Try again!</h2></p>\n')

    #     if "latex" in output.keys():
    #         output.latex = data['text/latex'].split('\n')

    def check_answer(self, output, answer):
        self.answer = answer
        if self.answer == self.correct_answer:
            return { 'points' : 5 , 'comments': 'Great job!' }
        else:
            return { 'points' : 0 , 'comments': 'Try again!' }
                
    def get_answer(self):
        return self.selected

    def set_answer(self, answer):
        if answer and answer not in list(self.choices):
            # will this get raised?
            raise ValueError('answer should be in choices! %s' % `(answer, self.choices)`)
        self.selected = answer

    answer = property(get_answer, set_answer)

class TrueFalse(MultipleChoice):

    checkable = True

    def __init__(self, identifier, question_text, correct_answer, 
                 assignment='assignment1', selected=None):
        MultipleChoice.__init__(self, identifier, question_text, ['True', 'False'],
                                str(correct_answer), assignment=assignment,
                                selected=selected)

    @property
    def constructor_info(self):
        args = [self.identifier, self.question_text, self.correct_answer]
        kw = {'assignment':self.assignment,
              'selected':self.selected}
        return ('true_false', args, kw)

class TextBox(MultipleChoice):

    checkable = True

    def __init__(self, identifier, question_text, correct_answer=None, 
                 assignment='assignment1', answer=''):
        self.identifier = identifier
        self.question_text = question_text
        self.correct_answer = correct_answer
        self.assignment = assignment
        self.answer = answer

    @property
    def constructor_info(self):
        args = [self.identifier, self.question_text]
        kw = {'correct_answer':self.correct_answer,
              'assignment':self.assignment,
              'answer':self.answer}
        return ('textbox', args, kw)

    def publish(self, return_data=False, display=True):
        latex_data = {'text/latex':self.question_text}

        d = {'identifier': self.identifier,
             'url': self.assignment,
             'answer':self.answer}

        textbox_code = '''
        <form method="post" name=%(identifier)s ><p><input type="text" value="%(answer)s"></p></form>
        ''' % d

        html_data = {'text/html': textbox_code}
        json_data = {'application/json':{'identifier':self.identifier,
                                         'constructor_info':self.constructor_info}}
        if display:
            # this puts the question identifier info in this output

            latex_data.update(json_data)
            publish_display_data("HomeworkBuilder", latex_data)

            html_data.update(json_data)
            publish_display_data("HomeworkBuilder", html_data)

        if return_data:
            data = {}
            for d in [latex_data, html_data, json_data]:
                data.update(d)
            return data

    def get_answer(self):
        return self._answer

    def set_answer(self, answer):
        self._answer = answer

    answer = property(get_answer, set_answer)

class NormalMean(object):

    """
    Sample from N(mean, sd) independently n times 
    """

    tol = 5.e-2
    checkable = True
    class_name = 'normal_mean'
    question_template = r"What is the sample mean, $\bar{X}$ of this sequence: %s ?"

    # use student json seed
    def __init__(self, identifier, mean, sd, n):
        self.mean = mean
        self.identifier = identifier
        self.sd = sd
        self.n = n
        self.sequence = self.generate()

    def generate(self):
        return np.round(np.random.standard_normal(self.n), 1) * self.sd + self.mean

    @property
    def correct_answer(self):
        return np.mean(self.sequence)

    def publish(self, return_data=False, display=True):
        latex_data = {'text/latex': self.question_template % `[float("%0.1f" % s) for s in self.sequence]`}
        html_data = {'text/html': '<form method="post" name=%s ><p><input type="text" ></p></form>' % self.identifier}
        json_data = {'application/json':{'identifier':self.identifier,
                                         'constructor_info': (self.class_name, [self.identifier, self.mean, self.sd, self.n], {})}}

        output_data = {}
        if display:
            # this puts the question identifier info in this output

            latex_data.update(json_data)
            publish_display_data("NormalMean", latex_data)

            html_data.update(json_data)
            publish_display_data("NormalMean", html_data)

        if return_data:
            data = {}
            for d in [latex_data, html_data, json_data]:
                        data.update(d)
            return data

    def check_answer(self, output, answer):
        self.answer = answer
        data = self.publish(return_data=True, display=False)
        if np.fabs(float(answer) - float(self.correct_answer)) / np.std(self.sequence) < self.tol:
            if "html" in output.keys():
                output.html = data['text/html'].split('\n')
                output.html.append('\n<p><h2>Good job!</h2></p>\n')
        elif self.answer:
            if "html" in output.keys():
                output.html = data['text/html'].split('\n')
                output.html.append('\n<p><h2>Try again with some new data!</h2></p>\n')

        if "latex" in output.keys():
            output.latex = data['text/latex'].split('\n')

  
def find_identified_outputs(cell, identifier):
    outputs = []
    if hasattr(cell, 'outputs'):
        for output in cell.outputs:
            if 'json' in output:
                try:
                    if ('identifier' in output.json.keys() and
                        output.json['identifier'] == identifier):
                            outputs.append(output)
                except AttributeError:
                    pass
    return outputs

def find_identified_cells(nb, identifier):
    """
    Find all cells in a notebook with a given identifier
    in their json output.

    """
    cells = []
    for ws in nb.worksheets:
        for cell in ws.cells:
            outputs = find_identified_outputs(cell, identifier)
            if outputs:
                cells.append(cell)
    return cells


def update_output(output, identifier, answer):
    """
    Create a question from an output, and modify it in place
    based on the given answer.
    """
    class_name, args, kw = output.json.constructor_info
    question = construct_question(class_name, args, kw)
    if question.checkable:
        question.check_answer(output, answer)

question_types = {'multiple_choice':MultipleChoice,
                  'true_false':TrueFalse,
                  'textbox':TextBox,
                  'normal_mean':NormalMean}

def register_question_type(name, constructor):
    import sys
    question_types[name] = constructor

def construct_question(name, args, keyword_args):
    return question_types[name](*args, **keyword_args)
