# coding: utf-8
# This file is a part of VK4XMPP transport
# © simpleApps, 2015.

findListByID = lambda id, list: [key for key in list if key["lid"] == id]

from __main__ import *
from __main__ import _

RosterSemaphore = threading.Semaphore()

class Roster:

	@staticmethod
	def getNode(jid, name=IDENTIFIER["name"], action="add"):
		return xmpp.Node("item", {"action": action, "jid": jid, "name": name})

	@classmethod
	@utils.threaded
	def manageRoster(cls, user, dist={}, action="add"):
		lists = user.vk.getLists()
		iq = xmpp.Iq("set", to=user.source, frm=TransportID)
		node = xmpp.Node("x", {"xmlns": xmpp.NS_ROSTERX}) 
		items = [cls.getNode(TransportID, action=action)]
		dist = dist or user.friends
		for uid, value in dist.iteritems():
			item = cls.getNode(vk2xmpp(uid), value["name"], action)
			if lists and value["lists"]:
				list = findListByID(value["lists"][0], lists)
				if list:
					item.setTagData("group", list[0]["name"])
			items.append(item)
		node.setPayload(items)
		iq.addChild(node=node)
		logger.debug("RosterManager: sending %s fellas to user (jid: %s)", len(items), user)
		with RosterSemaphore:
			sender(Component, iq, cb=user.markRosterSet)
			user.sendSubPresence(user.friends)

	@classmethod
	def checkRosterx(cls, user, resource):
		"""
		Checks if the client supports XEP-0144: Roster Item Exchange
		If it doesn't, or it didn't answer us, then transport will use the old method
		"""
		jid = "%s/%s" % (user.source, resource)
		sendPresence(jid, TransportID, "subscribe", IDENTIFIER["name"])
		sendPresence(jid, TransportID, nick=IDENTIFIER["name"],
			reason=_("You are being initialized, please wait..."), show="xa")
		def answer(cl, stanza):
			if xmpp.isResultNode(stanza):
				query = stanza.getTag("query")
				if query.getTags("feature", attrs={"var": xmpp.NS_ROSTERX}):
					cls.manageRoster(user, user.friends)
				else:
					user.sendSubPresence(user.friends)

		iq = xmpp.Iq("get", to=jid, frm=TransportID)
		iq.addChild("query", namespace=xmpp.NS_DISCO_INFO)
		sender(Component, iq, cb=answer)