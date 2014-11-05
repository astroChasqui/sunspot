from flask.ext.wtf import Form
from wtforms import SelectField, SubmitField, IntegerField, BooleanField, FieldList, FormField
from wtforms.validators import InputRequired, NumberRange


class DateForm(Form):
    year = SelectField(choices = [(x, x) for x in range(2001, 2014+1)],
                       coerce=int)
    month = SelectField(choices = [(x, x) for x in range(1, 12+1)],
                        coerce=int)
    day = SelectField(choices = [(x, x) for x in range(1, 31+1)],
                      coerce=int)
    submit = SubmitField('Submit')

class InstructorForm(Form):
    number_of_students = IntegerField('How many students do you have?',
                                      validators=[InputRequired(),
                                                  NumberRange(5, 100)])
    dates_per_student = IntegerField('How many pictures would you like '+
                                     'each student to work on?',
                                      validators=[InputRequired(),
                                                  NumberRange(1, 10)])
    generate_csv = BooleanField('Generate files')
    submit = SubmitField('Submit')

class StudentForm(Form):
    number_of_dates = IntegerField('How many dates were you assigned?',
                                   validators=[InputRequired(),
                                               NumberRange(1, 10)])
    submit = SubmitField('Submit')
    dates = FieldList(FormField(DateForm))

    def add_dates(self, number_of_dates):
        for i in range(number_of_dates):
            self.dates.append_entry()
