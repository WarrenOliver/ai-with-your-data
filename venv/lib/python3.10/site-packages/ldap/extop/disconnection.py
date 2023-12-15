"""
ldap.extop.disconnection - Class for Notice of Disconnection
Unsolicited Notification (see RFC4511)

See https://www.python-ldap.org/ for details.
"""

from ldap.response import UnsolicitedNotification


class NoticeOfDisconnection(UnsolicitedNotification):
    responseName = "1.3.6.1.4.1.1466.20036"
