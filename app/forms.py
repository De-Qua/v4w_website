from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import Optional, DataRequired, ValidationError, Email, EqualTo, Length

class FeedbackForm(FlaskForm):
    name = StringField('Nome')
    email = StringField('Email', validators=[Optional(), Email()])
    category = SelectField('Oggetto',choices=[(0,"Oggetto non specificato"),(1,"Indirizzo sbagliato"),(2,"Strada sbagliata"),(3,"Problemi di grafica"),(4,"Proposta di miglioramento"),(5,"Altro")], default=0, coerce=int)
    searched_string = StringField('Ricerca')
    searched_start = StringField('Partenza')
    searched_end = StringField('Arrivo')
    found_string = StringField('Risultato')
    found_start = StringField('Risultato partenza')
    found_end = StringField('Risultato arrivo')
    feedback = TextAreaField('Problema o feedback')
    dictJS = StringField("Dict JS")
    start_coord_fb = StringField("Coordinata di Partenza")
    end_coord_fb = StringField("Coordinata d'arrivo")
    submit = SubmitField('Invia')
