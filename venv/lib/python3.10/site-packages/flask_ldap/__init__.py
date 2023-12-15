# coding=utf-8
import os

__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2013, Dmitry Zhiltsov"
__license__ = "BSD "

from functools import wraps
from string import capwords

import ldap
from flask import current_app, request, flash, render_template


# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack
from flask import session, redirect, url_for


FIELDS = (
    'sAMAccountName',
    'distinguishedName', # 'ad_cn',

    'givenName', # 'first_name'
    'sn', # 'last_name',
    'middleName', # 'middle_name',
    'description', # 'full_name',
    'memberOf',

    'company', # 'company',
    'department', # 'department',
    'title', # 'title',
    'manager', # 'manager',

    'cn', # 'name_lat',
    'name', # 'name_lat',
    'displayName', # 'display_name',
    'displayNamePrintable',

    # 'comment',            # 'gender',
    'primaryTelexNumber', # 'birth_date',  # дата рождения

    'employeeID', # 'employee_id',
    'mail', # 'mail',
    'mobile', # 'mobile',
    'streetAddress', # 'location',
    'ipPhone',
)


class LDAP(object):
    def __init__(self, app=None, mongo=None):
        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

        if mongo is not None:
            self.mongo = mongo
        else:
            self.mongo = None

    def init_app(self, app):
        app.config.setdefault('LDAP_HOST', '127.0.0.1')
        app.config.setdefault('LDAP_PORT', 389)
        app.config.setdefault('LDAP_SCHEMA', 'ldap')
        app.config.setdefault('LDAP_DOMAIN', 'example.com')
        app.config.setdefault('LDAP_LOGIN_VIEW', 'login')
        app.config.setdefault('LDAP_SEARCH_BASE', 'OU=Users,DC=example,DC=com')
        app.config.setdefault('LDAP_LOGIN_TEMPLATE', 'login.html')
        app.config.setdefault('LDAP_SUCCESS_REDIRECT', 'index')
        app.config.setdefault('LDAP_PROFILE_KEY', 'sAMAccountName')
        app.config.setdefault('LDAP_AVATAR_LOC', None)
        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

        self.login_func = app.config['LDAP_LOGIN_VIEW']

    def connect(self):
        print self.app.config['LDAP_HOST']
        self.conn = ldap.initialize('{0}://{1}:{2}'.format(
            self.app.config['LDAP_SCHEMA'],
            self.app.config['LDAP_HOST'],
            self.app.config['LDAP_PORT']))
        return self.conn

    def teardown(self, exception):
        ctx = stack.top
        if hasattr(ctx, 'ldap_host'):
            ctx.ldap_host.close()

    def ldap_query(self, query):
        fields = list(FIELDS)
        if fields and not 'sAMAccountName' in fields:
            fields.append('sAMAccountName')
        if fields and self.app.config['LDAP_AVATAR_LOC']:
            fields.append('jpegPhoto')
            if 'LDAP_PROFILE_KEY' in self.app.config:
                pass
            else:
                fields.append('userPrincipalName')
        records = self.conn.search_s(self.app.config['LDAP_SEARCH_BASE'],
                                    ldap.SCOPE_SUBTREE, query, fields)
        # except ldap.LDAPError as e:
        #     flash(message=dict(e.message)['desc'], category='error')
        #     return False
        self.conn.unbind_s()
        res = []
        for rec in records:
            if rec[0] is None:
                continue
            newrec = {}
            for field in rec[1].keys():
                try:
                    newrec[field] = rec[1][field][0] if len(rec[1][field]) == 1 else rec[1][field]
                except:
                    newrec[field] = None
            res.append(newrec)
        if 'jpegPhoto' in res[0]:
            self.jpegPhoto = res[0]['jpegPhoto']
            if 'LDAP_PROFILE_KEY' in self.app.config:
                self.userPrincipalName = res[0][self.app.config['LDAP_PROFILE_KEY']]
            else:
                self.userPrincipalName = res[0]['userPrincipalName']
        else:
            self.jpegPhoto = None
            self.userPrincipalName = None
        return res

    def ldap_login(self, username, pwd):
        try:
            self.connect()
            user = "{0}@{1}".format(username, self.app.config['LDAP_DOMAIN'])
            self.conn.set_option(ldap.OPT_REFERRALS, 0)
            self.conn.simple_bind_s(user, pwd.encode('utf8'))
            query = "sAMAccountName=%s" % username
            for user in self.ldap_query(query):
                mu = dict(_id=user[self.app.config['LDAP_PROFILE_KEY']])
                mu['username'] = user.get('sAMAccountName')
                mu['memberOf'] = user.get('memberOf')
                mu['ad_cn'] = user.get('distinguishedName')
                mu['fired'] = 'OU=Retired' in mu['ad_cn']
                mu['staff'] = True

                mu['last_name'] = capwords(user.get('sn', '').decode('utf8'))
                mu['first_name'] = capwords(user.get('givenName', '').decode('utf8'))
                mu['middle_name'] = capwords(user.get('middleName', '').decode('utf8'))

                mu['full_name'] = capwords(user.get('description', '').decode('utf8'))
                mu['short_name'] = short_name(user)
                mu['lat_name'] = user.get('displayNamePrintable',
                                          user.get('displayName', '').split(' (')[0])

                mu['company'] = user.get('company')
                mu['department'] = user.get('department')
                mu['title'] = user.get('title')
                mu['manager'] = user.get('manager')

                mu['mobile'] = user.get('mobile')
                mu['mail'] = user.get('mail')
                mu['location'] = user.get('streetAddress')
                mu['ip_phone'] = user.get('ipPhone')

                if self.mongo is not None:
                    self.mongo.db.users.save(mu), mu['full_name']
                self.mu = mu
                self.save_avatar()

            if self.app.config['LDAP_REQUIRED_GROUP'] is not None:
                if self.app.config['LDAP_REQUIRED_GROUP'] not in self.mu['memberOf']:
                    flash(u"Login successful but not authorized.")
                    return False

            session['username'] = username
            return True

        except ldap.LDAPError as e:
            return self.ldap_err(e)
        except Exception as e:
            return self.other_err(e)

    def save_avatar(self):
        if self.app.config['LDAP_AVATAR_LOC']:
            avatar_file = open(os.path.join(self.app.config['LDAP_AVATAR_LOC'],self.userPrincipalName+'.jpg'), 'wb')
            avatar_file.write(self.jpegPhoto)
            avatar_file.close()

    def login(self):
        """
        View function for rendering and logic for auth form

        :return:
        """
        if request.method == 'POST':
            if "username" in request.form and "password" in request.form:
                if self.ldap_login(request.form['username'], request.form['password']):
                    for i in self.mu.keys():
                        session[i] = self.mu[i]
                    return redirect(url_for(self.app.config['LDAP_SUCCESS_REDIRECT']))
                else:
                    return render_template(self.app.config['LDAP_LOGIN_TEMPLATE'])
        if 'username' in session:
            flash(u"You allready login in {0}".format(session['username']))
        return render_template(self.app.config['LDAP_LOGIN_TEMPLATE'])

    def ldap_err(self, exc):
        flash(message=dict(exc.message)['desc'], category='error')
        return False

    def other_err(self, exc):
        flash(message=exc.message, category='error')
        return False

    @property
    def connection(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'ldap_host'):
                ctx.ldap_host = self.connect()
            return ctx.ldap_host


def login_required(f):
    """
    Decorator for views that require login.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        return redirect(url_for(current_app.config['LDAP_LOGIN_VIEW']))

    return decorated


def short_name(user):
    """
    Make short name
    """
    fn = user.get('description', '').decode('utf8').split(' ')
    ln = user.get('sn', fn[0].encode('utf8')).decode('utf8')
    gn = user.get('givenName', '').decode('utf8')
    mn = user.get('middleName', '').decode('utf8')
    sn = [ln, ]
    gn = gn or fn[-2] if len(fn) > 2 else fn[-1]

    if gn:
        sn.append(u'{0}.'.format(gn[0]))
    mn = mn or fn[-1] if len(fn) > 2 else ''

    if mn:
        sn.append(u'{0}.'.format(mn[0]))

    return u' '.join(sn).encode('utf8')
