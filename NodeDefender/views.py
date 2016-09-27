'''
Copyright (c) 2016 Connection Technology Systems Northern Europe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE
SOFTWARE.
'''
from . import app, LoginMan, db, icpe, chconf, mqtt
from flask import render_template, request, flash, redirect, url_for, abort, \
json
from flask_login import login_required, login_user, current_user, logout_user
from .models import UserModel, iCPEModel, MessageModel, LoginLogModel,\
NodeEventModel, NodeHeatStatModel, NodePowerStatModel
from .forms import NodeForm, LoginForm, RegisterForm, AdminServerForm
from datetime import datetime

# Welcome Text that should be added when new user is added.
WelcomeText = "Welcome to NodeDefender {} \n \
This is currently in rapid development with new features coming out \
every week. Please keep yourself updated on github to stay in touch \
with the new features and report any issues or request features that \
you wish to see. \n \
You can contact me on henrik.nilsson@ctsystem.se \
\n \n \
Best Regards, Henrik"

'''
Login Page for Unauthorized users.
When logged in the achive a cookie that is later used for RESTful API calls
that load data to the webpage
'''

@LoginMan.user_loader
def load_user(id):      # Needed for Flask-login to work.
    return UserModel.query.get(int(id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # If Method is GET is should display login-page
    if request.method == 'GET':
        lform = LoginForm()
        rform = RegisterForm()
        return render_template('login.html', lform = lform, rform = rform)

    lform = LoginForm(request.form)
    # login-stuff to verify if user is correct
    if lform.validate():
        user = UserModel.query.filter_by(email = lform.email.data).first()
        if user is None:
            flash('User or password is invalid', 'error')
            return redirect(url_for('login'))
        if not user.verify_password(lform.password.data, request.remote_addr):
            loginlog = LoginLogModel(False, request.remote_addr,
                                    request.user_agent)
            user.loginlog.append(loginlog)
            db.session.add(user)
            db.session.commit()
            flash('User or password is invalid', 'error')
            return redirect(url_for('login'))
        loginlog = LoginLogModel(True, request.remote_addr,
                                request.user_agent)
        user.loginlog.append(loginlog)
        user.last_login = datetime.now()
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=lform.remember_me())
        return redirect(url_for('index'))
    else:
        flash("Please fill in correctly", "error")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    rform = RegisterForm(request.form)
    if rform.validate():
        UserQuery = UserModel.query.filter_by(email =\
                                              rform.email.data).first()
        if UserQuery is not None:
            flash('Email is already present', 'error')
            return redirect(url_for('login'))
        user = UserModel(rform.firstname.data.capitalize(),
                rform.lastname.data.capitalize(), rform.email.data, \
                rform.password.data)
        WelcomeMessage = MessageModel(subject="Welcome {}!".format(user.firstname), \
                              body=WelcomeText.format(user.firstname))
        # Adds initial Mail to mailbox, welcoming new user.
        user.messages.append(WelcomeMessage)
        db.session.add(user)
        db.session.commit()
        flash('user successfully added', 'success')
        return redirect(url_for('login'))
    else:
        flash('something went wrong in form', 'error')
        return redirect(url_for('login'))


@app.context_processor
def inject_user():      # Adds general data to base-template
    if current_user.is_authenticated:
        # Return Message- inbox for user if authenticated
        messages = UserModel.query.get(current_user.id).messages
        return dict(user = current_user, messages = messages)
    else:
        # If not authenticated user get Guest- ID(That cant be used).
        return dict(user = current_user)

'''
Below is all the pages deliverd to Logged in Users.
All pages are pretty much only sent out without any special data except for a
cookie. Data is later filled in via AJAX from Webpage
'''

@app.route('/')
@app.route('/index')
@login_required
def index():
    nodelist = []
    nodes = iCPEModel.query.all()
    # Staticlly configured data. Just for demo...
    heat = {'Current' : '23.2', 'Daily' : '23.1', 'Weekly' : '24.2', \
            'Monthly' : '24.4'}
    power = {'Current' : '1249', 'Daily' : '1600', 'Weekly' : '1320', \
             'Monthly' : '1410'}
    events = {'Current' : '0', 'Daily' : '124', 'Weekly' : '110', \
              'Monthly' : '78'}
    for node in nodes:
        nodelist.append({'alias' : node.alias, 'mac' : node.mac,
                         'lat' : node.location.geolat, 'long' : node.location.geolong})
    nodeevents = NodeEventModel.query.order_by('created_on desc').limit(20)
    return render_template('index.html', nodelist=nodes, heat = heat, \
                           power = power, events = events, nodeevents =
                           nodeevents)

#
# User specific profile-views
#

@app.route('/user/profile')
@login_required
def UserProfile():
    Profile = UserModel.query.filter_by(email = current_user.email).first()
    Team =  UserModel.query.all()
    return render_template('user/profile.html', Team = Team, Profile = Profile)

@app.route('/user/inbox')
@login_required
def UserInbox():
    return render_template('user/inbox.html')

@app.route('/user/inbox/<mailid>', methods=['GET', 'POST'])
@login_required
def UserInboxID(mailid):
    message = MessageModel.query.filter_by(uuid=mailid).first()
    return render_template('user/inboxid.html', mailid=mailid, message =
                           message)

@app.route('/user/settings')
@login_required
def UserSettings():
    return render_template('user/settings.html')

#
# Views for Nodes- view
#

@app.route('/nodes/list', methods=['GET', 'POST'])
@login_required
def NodesList():
    if request.method == 'GET':
        nodes = iCPEModel.query.all()
        return render_template('nodes/list.html', nodes = nodes)
    try:
        icpe.AddiCPE(request.form['mac'], request.form['alias'],
              request.form['street'], request.form['city'])
        flash('Succesfully added node: ' + request.form['mac'], 'success')
        return redirect(url_for('NodesList'))
    except Exception as e:
        flash('Error in adding node: ' + request.form['mac'] + '. ' + str(e), 'danger')
        return redirect(url_for('NodesList'))

@app.route('/nodes/events')
@login_required
def NodesEvents():
    return render_template('nodes/events.html')

@app.route('/nodes/list/<mac>', methods=['GET', 'POST'])
@login_required
def NodesNode(mac):
    iCPE = iCPEModel.query.filter_by(mac = mac).first()
    if not iCPE:
        raise ValueError('Cant find mac')
    form = NodeForm()
    if request.method == 'GET':
        znodes = icpe.WebForm(mac)
        '''
        powerstat = dict((nodeid, list(events)) for nodeid, events in
                    groupby(iCPE.powerstat, lambda stat: stat.nodeid))
        '''
        return render_template('nodes/node.html', mac=mac, form=form, iCPE =
                               iCPE, znodes = znodes)
    if form.validate():
        print(form.NodeField.data)
    return render_template('nodes/node.html', mac=mac, form=form, iCPE = iCPE)

@app.route('/nodes/<mac>/update')
@login_required
def NodesUpdate(mac):
    if not mqtt():
        flash('MQTT is Offline', 'danger')
    else:
        icpe.Event(mac, 'UpdateNode')
        flash('Node ' + mac + ' succesfully updated.', 'success')
    return redirect(url_for('NodesNode',  mac=mac))

@app.route('/nodes/<mac>/include')
@login_required
def NodesInclude(mac):
    if not mqtt():
        flash('MQTT is Offline', 'danger')
    else:
        icpe.Event(mac, 'NodeInclude')
        flash('Node '  + mac + ' in Include for 30sec', 'success')
    return redirect(url_for('NodesNode', mac=mac))

@app.route('/nodes/<mac>/exclude')
@login_required
def NodesExclude(mac):
    if not mqtt():
        flash('MQTT is Offline', 'danger')
    else:
        icpe.Event(mac, 'NodeExclude')
        flash('Node ' + mac + ' in Exclude for 30sec', 'success')
    return redirect(url_for('NodesNode', mac=mac))

@app.route('/nodes/<mac>/delete')
@login_required
def DeleteNode(mac):
    try:
        icpe.DeleteiCPE(mac)
        flash('Node: ' + mac + ' successfully deleted', 'success')
        return redirect(url_for('NodesList'))
    except Exception as e:
        flash('Unable to remove ' + str(mac) + '. Error: ' + str(e), 'danger')
        return redirect(url_for('NodesList'))

#
# Views for Data- view
#

@app.route('/data/power')
def DataPower():
    if request.method == 'GET':
        stats = NodePowerStatModel.query.all()
        return render_template('data/power.html', stats = stats)

@app.route('/data/heat')
def DataHeat():
    if request.method == 'GET':
        stats = NodeHeatStatModel.query.all()
        return render_template('data/heat.html', stats = stats)


#
# Views for Admin- view
#
@app.route('/admin/server')
@login_required
def AdminServer():
    if request.method == 'GET':
        sform = AdminServerForm()
        return render_template('admin/server.html', sform = sform)

@app.route('/admin/sever/setgeneral', methods=['GET', 'POST'])
@login_required
def AdminServerSetGeneral():
    sform = AdminServerForm(request.form)
    if sform.validate():
        flash('Successfully updated General Settings', 'success')
        return redirect(url_for('AdminServer'))
    else:
        flash('Error when trying to update General Settings', 'danger')
        return redirect(url_for('AdminServer'))

@app.route('/admin/users')
@login_required
def AdminUsers():
    return render_template('admin/users.html')

@app.route('/admin/mqtt')
@login_required
def AdminMqtt():
    return render_template('admin/mqtt.html')

@app.route('/admin/backup')
@login_required
def AdminBackup():
    return render_template('admin/backup.html')

'''
error handlers
'''

@app.errorhandler(403) # Trying to access without permission
@login_required
def page_not_allowed(e):
    return render_template('403.html'), 403

@app.errorhandler(404) # Trying to access page that does not exist.
@login_required
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500) # Internal Server Error
@login_required
def internal_server_error(e):
    return render_template('500.html'), 500
