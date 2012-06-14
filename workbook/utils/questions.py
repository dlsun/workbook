import numpy as np
from IPython.core.displaypub import publish_display_data
import json

class HomeworkCounter(object):

    def __init__(self):
        self.question_number = 0

    def next(self):
        self.question_number += 1
        publish_display_data("HomeworkBuilder", {'text/html':"<h2>Question %d</h2>" % self.question_number})


def publish_workbook_metadata(metadata):
    publish_display_data("HomeworkBuilder", 
                         {"application/json":{"workbook_metadata":
                                                  metadata}})


class Question(object):

    def publish(self, return_data=False):
        raise NotImplementedError

    @property
    def constructor_info(self):
        return None

    def set_answer(self):
        raise NotImplementedError

    def get_answer(self):
        raise NotImplementedError

    answer = property(get_answer, set_answer)

    def check_answer(self, answer):
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
        self.assignment = assignment
        self.identifier = identifier

    @property
    def constructor_info(self):
        args = [self.identifier, self.question_text, self.choices, self.correct_answer]
        kw = {'assignment':self.assignment,
              'selected':self.selected}
        return ('multiple_choice', args, kw)

    def publish(self, return_data=False):

        latex_data = {'text/latex':self.question_text}

        publish_display_data("HomeworkBuilder", latex_data)

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
        json_data = {'application/json': {'question_identifier':self.identifier,
                                          'constructor_info':self.constructor_info}}

        publish_display_data("HomeworkBuilder", html_data)
        publish_display_data("HomeworkBuilder", json_data)

        if return_data:
            data = {}
            for d in [latex_data, html_data, json_data]:
                data.update(d)
            return data

    def check_answer(self, answer):
        self.answer = answer
        data = self.publish(return_data=True)
        if self.answer == self.correct_answer:
            data['text/html'] += '\n<p><h2>Good job!</h2></p>\n'
        elif self.answer:
            data['text/html'] += '\n<p><h2>Try again!</h2></p>\n'
        return data

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

    def publish(self, return_data=False):
        latex_data = {'text/latex':self.question_text}
        publish_display_data("HomeworkBuilder", latex_data)

        d = {'identifier': self.identifier,
             'url': self.assignment,
             'answer':self.answer}

        textbox_code = '''
        <form method="post" name=%(identifier)s ><p><input type="text" value="%(answer)s"></p></form>
        ''' % d

        html_data = {'text/html': textbox_code}
        json_data = {'application/json':{'question_identifier':self.identifier,
                                         'constructor_info':self.constructor_info}}
        publish_display_data("HomeworkBuilder", html_data)
        publish_display_data("HomeworkBuilder", json_data)

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

    def check_answer(self, answer):
        self.answer = answer
        data = self.publish(return_data=True)
        if self.answer == self.correct_answer:
            data['text/html'] += '\n<p><h2>Good job!</h2></p>\n'
        elif self.answer:
            data['text/html'] += '\n<p><h2>Try again!</h2></p>\n'
        return data

def is_identified_cell(cell, identifier):
    if hasattr(cell, 'outputs'):
        for output in cell.outputs:
            if 'json' in output:
                try:
                    if 'question_identifier' in output.json.keys():
                        if output.json['question_identifier'] == identifier:
                            return True, output
                except AttributeError:
                    pass
    return False, None

def find_identified_cell(nb, identifier):
    for ws in nb.worksheets:
        for cell in ws.cells:
            check, value = is_identified_cell(cell, identifier)
            if check:
                return cell, value
    return None, None

question_types = {'multiple_choice':MultipleChoice,
                  'true_false':TrueFalse,
                  'textbox':TextBox}

def register_question_type(name, constructor):
    question_types[name] = constructor

def construct_question(name, args, keyword_args):
    return question_types[name](*args, **keyword_args)
