from flask import Flask, render_template, request, redirect, url_for, session,\
                  send_file
from forms import DateForm, InstructorForm, StudentForm
import datetime
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'manchas solares'

fpath = os.path.dirname(os.path.realpath(__file__))

# Uncomment at deploy
'''
class WebFactionMiddleware(object):
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        environ['SCRIPT_NAME'] = '/projects/sunspot'
        return self.app(environ, start_response)

app.wsgi_app = WebFactionMiddleware(app.wsgi_app)
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('date'):
        date = datetime.date.today()
    else:
        date = datetime.date.fromordinal(session.get('date'))
    form = DateForm(year=date.year, month=date.month, day=date.day)
    if request.method == 'POST':
        date = datetime.date(form.year.data,
                             form.month.data,
                             form.day.data)
        session['date'] = date.toordinal()
        return redirect(url_for('index'))
    else:
        session.clear()
        img = get_img(date)
        if not img:
            img = get_img(date - datetime.timedelta(days=1))
        return render_template('index.html', form = form,
                               date = date, img = img)

@app.route('/student', methods=['GET', 'POST'])
def student():
    form = StudentForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            session['number_of_dates'] = form.number_of_dates.data
            if form.dates:
                dates = []
                images = []
                for date in form.dates:
                    datex = datetime.date(date.year.data,
                                          date.month.data,
                                          date.day.data)
                    dates.append(datex.toordinal())
                    images.append(get_img(datex))
                session["dates"] = dates
                session["images"] = images
                return redirect(url_for('student'))
            return redirect(url_for('student'))
        else:
            return render_template('student.html', form = form)
    elif request.method == 'GET':
        if session.get('number_of_dates'):
            form.add_dates(session.get('number_of_dates'))
        form.number_of_dates.data = session.get('number_of_dates')
        if session.get('dates'):
            dates = [datetime.date.fromordinal(date)
                     for date in session.get('dates')]
        else:
            dates = None
        images = session.get('images')
        if images:
            images = zip(dates, images)
        return render_template('student.html', form = form,
                               images = images)

@app.route('/instructor', methods=['GET', 'POST'])
def instructor():
    form = InstructorForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if form.generate_csv.data:
                dates = [datetime.date.fromordinal(date)
                         for date in session.get('dates')]
                ssn = session.get('ssn')
                students = session.get('students')*\
                           session.get('dates_per_student')
                x = ["{0},{1},{2}\n".format(d, st, s)
                     for d, s, st in zip(dates, students, ssn)]
                y = ["{0},{1}\n".format(d, s)
                     for d, s in zip(dates, students)]
                fname = session.get('fname').split('.')[0]
                ifname = os.path.join(fpath, 'static', 'files', fname+'i.csv')
                sfname = os.path.join(fpath, 'static', 'files', fname+'s.csv')
                with open(ifname, 'w') as csv:
                    csv.write('Date,Official SSN,Student\n'+''.join(x))
                with open(sfname, 'w') as csv:
                    csv.write('Date,Student\n'+''.join(y))
                figname = os.path.join(fpath, 'static', 'files', fname+'.png')
                zname = os.path.join(fpath, 'static', 'files', fname+'.zip')
                os.system("zip -j {0} {1} {2} {3}".\
                          format(zname, ifname, sfname,figname))
                os.system("printf '@ "+fname+\
                          "i.csv\n@=instructor.csv\n' | zipnote -w "+zname)
                os.system("printf '@ "+fname+\
                          "s.csv\n@=students.csv\n' | zipnote -w "+zname)
                os.system("printf '@ "+fname+\
                          ".png\n@=date_vs_ssn.png\n' | zipnote -w "+zname)
                return send_file(zname, as_attachment=True,
                                 attachment_filename="sunspot_project.zip")
            
            ns = form.number_of_students.data
            dps = form.dates_per_student.data
            nd = np.random.random_integers(-7, 7)
            xi = datetime.date(2001, 10, 1+7) + datetime.timedelta(days=nd)
            xf = datetime.date(2013, 9, 30)
            dd = (xf - xi)/(ns * dps)
            dates = [xi + i*dd for i in range(ns*dps)]
            ssn_file = os.path.join(fpath, 'ISSN_D_tot.csv')
            ssd = np.genfromtxt(ssn_file, delimiter=',').transpose()
            ssn = [str(get_ssn(dates[i], ssd)) for i in range(ns*dps)]
            plt.figure(figsize=(5,4))
            plt.plot(dates, ssn, 'bo')
            plt.xlabel('Date')
            plt.ylabel('Sunspot number')
            plt.ylim(0., 200.)
            plt.tight_layout()
            fname = datetime.datetime.now().strftime("%Y%m%d-%H%M%S.png")
            ssn_fig = os.path.join(fpath, 'static', 'files', fname)
            plt.savefig(ssn_fig)
            plt.close()
            session['number_of_students'] = ns
            session['students'] = [str(i+1) for i in range(ns)]
            session['dates_per_student'] = dps
            session['ssn_fig'] = 'static/files/'+fname
            session['fname'] = fname
            session['dates'] = [date.toordinal() for date in dates]
            session['ssn'] = ssn
            return redirect(url_for('instructor'))
        else:
            return render_template('instructor.html', form = form,
                               ssn_fig = None)
    elif request.method == 'GET':
        form.number_of_students.data = session.get('number_of_students')
        form.dates_per_student.data = session.get('dates_per_student')
        ssn_fig = session.get('ssn_fig')
        return render_template('instructor.html', form = form,
                               ssn_fig = ssn_fig)


@app.route('/help')
def help():
    return render_template('help.html')


import httplib
def exists(site, path):
    conn = httplib.HTTPConnection(site)
    conn.request('HEAD', path)
    response = conn.getresponse()
    conn.close()
    return response.status == 200

def get_img(date):
    site = "sohowww.nascom.nasa.gov"
    location = "/data/synoptic/sunspots/"
    # Pictures exist from 20011001 to 20110113 and from 20110307
    if date >= datetime.date(2011, 03, 07):
        fname = "sunspots_512_"+str(date).replace("-", "")+".jpg"
    else:
        fname = "sunspots_"+str(date).replace("-", "")+".jpg"
    if exists(site, location+fname):
        return "http://"+site+location+fname
    else:
        return None

def get_ssn(date, ssd):
    year, month, day = ssd[0], ssd[1], ssd[2]
    k = (year==date.year) & (month==date.month) & (day==date.day)
    if k.any():
        return ssd[4][k][0]
    else:
        return None


