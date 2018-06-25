"""
Copyright (c) 2018 Genome Research Ltd.

Author: Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import base64

from api import ldap
from common import types as T
from common.logging import Level, log
from common.utils import maybe
from ._adaptors import Attribute, flatten, to_bool
from ._bases import BaseNode, BaseRegistry, NoMatches
from ._mixins import Hypermedia


class Person(BaseNode):
    """ High level LDAP person model """
    _rdn_attr = "uid"
    _base_dn = "ou=people,dc=sanger,dc=ac,dc=uk"
    _object_classes = ["posixAccount"]

    _base_uri = "/people"

    _registry:BaseRegistry

    @staticmethod
    def decode_photo(jpegPhoto) -> T.Optional[bytes]:
        """ Adaptor that returns the decoded JPEG data, if it exists """
        if jpegPhoto is None:
            return None

        # TODO? Return an async generator instead; is that overkill?
        jpeg, *_ = map(base64.b64decode, jpegPhoto)
        return jpeg

    @staticmethod
    def is_human(sangerAgressoCurrentPerson) -> bool:
        """ Adaptor to determine the humanity of a given entry  """
        return maybe(to_bool)(sangerAgressoCurrentPerson) is not None

    @staticmethod
    def is_active(sangerAgressoCurrentPerson, sangerActiveAccount) -> bool:
        """ Adaptor to determine the active status of a given entry """
        return maybe(to_bool)(sangerAgressoCurrentPerson) or maybe(to_bool)(sangerActiveAccount)

    def __init__(self, uid:str, registry:BaseRegistry) -> None:
        attr_map = {
            "id":     Attribute("uid", adaptor=flatten),
            "name":   Attribute("cn", adaptor=flatten),
            "mail":   Attribute("mail", adaptor=flatten),
            "title":  Attribute("title", adaptor=maybe(flatten)),
            "photo":  Attribute("jpegPhoto", adaptor=Person.decode_photo),
            "human":  Attribute("sangerAgressoCurrentPerson", adaptor=Person.is_human),
            "active": Attribute("sangerAgressoCurrentPerson", "sangerActiveAccount", adaptor=Person.is_active)
        }

        self._registry = registry
        super().__init__(uid, registry.server, attr_map, registry.shelf_life)

    async def __serialisable__(self) -> T.Any:
        attrs = ["last_updated", "name", "mail", "title", "human", "active"]
        output = {attr: getattr(self, attr) for attr in attrs}

        output["id"] = Person.href(self, rel="self", value=self.id)

        # Link to photo, if it exists
        if self.photo is not None:
            class _Photo(Hypermedia):
                """ Dummy photo hypermedia entity """
                _base_uri = f"{self._base_uri}/{self._identity}"

                @property
                def identity(self) -> str:
                    return "photo"

            output["photo"] = Person.href(_Photo(), rel="photo")

        # Group involvement
        involvement = []
        for gid in self._registry.keys(Group):
            group = await self._registry.get(Group, gid)

            if await group.is_pi(self):
                involvement.append(Group.href(group, rev="pi", value=group.name))

            if await group.is_owner(self):
                involvement.append(Group.href(group, rev="owner", value=group.name))

            if await group.is_member(self):
                involvement.append(Group.href(group, rev="member", value=group.name))

        output["involvement"] = involvement

        return output


class Group(BaseNode):
    """ High level LDAP Human Genetics Programme group model """
    _rdn_attr = "cn"
    _base_dn = "ou=group,dc=sanger,dc=ac,dc=uk"
    _object_classes = ["posixGroup", "sangerHumgenProjectGroup"]

    _base_uri = "/groups"

    _registry:BaseRegistry

    def get_people(self, dns) -> T.Coroutine:
        """ Adaptor to resolve a list of Person DNs """
        async def _resolver():
            for dn in map(lambda x: x.decode(), dns or []):
                try:
                    rdn = Person.extract_rdn(dn)
                    yield await self._registry.get(Person, rdn)

                except ldap.NoSuchDistinguishedName:
                    # Invalid Person DN in group LDAP record
                    log(f"Group {self._identity} refers to an invalid person, with DN \"{dn}\"; please correct {self.dn}", Level.Warning)

                except NoMatches:
                    # No matching Person found
                    log(f"Group {self._identity} refers to an irresolvable person, with ID \"{rdn}\"; please correct {self.dn}", Level.Warning)

        return _resolver

    def get_person(self, dn) -> T.Coroutine:
        """ Adaptor to resolve a single Person, if there is one """
        async def _resolver():
            if dn is None:
                return None

            assert len(dn) == 1
            async for person in self.get_people(dn)():
                return person

        return _resolver

    @staticmethod
    def decode_prelims(sangerPrelimID) -> T.List[str]:
        """ Adaptor to decode the list of Prelim IDs """
        return [prelim.decode() for prelim in sangerPrelimID or []]

    def __init__(self, cn:str, registry:BaseRegistry) -> None:
        attr_map = {
            "name":        Attribute("cn", adaptor=flatten),
            "active":      Attribute("sangerHumgenProjectActive", adaptor=to_bool),
            "pi":          Attribute("sangerProjectPI", adaptor=self.get_person),
            "owners":      Attribute("owner", adaptor=self.get_people),
            "members":     Attribute("member", adaptor=self.get_people),
            "description": Attribute("description", adaptor=maybe(flatten)),
            "prelims":     Attribute("sangerPrelimID", adaptor=Group.decode_prelims)
            # sangerHumgenDataSecurityLevel
            # sangerHumgenProjectStorageResources
            # sangerHumgenProjectStorageQuotas
        }

        self._registry = registry
        super().__init__(cn, registry.server, attr_map, registry.shelf_life)

    async def __serialisable__(self) -> T.Any:
        attrs = ["last_updated", "active", "description", "prelims"]
        output = {attr: getattr(self, attr) for attr in attrs}

        output["id"] = Group.href(self, rel="self", value=self.name)

        pi = await self.pi()
        output["pi"] = Person.href(pi, rel="pi", value=pi.name)

        owners = []
        async for owner in self.owners():
            owners.append(Person.href(owner, rel="owner", value=owner.name))

        members = []
        async for member in self.members():
            members.append(Person.href(member, rel="member", value=member.name))

        output["owners"] = owners
        output["members"] = members

        return output

    async def _is_involved(self, who:Person, capacity:str) -> bool:
        """ Check a Person's involvement in a group """
        if capacity == "pi":
            pi = await self.pi()
            return who == pi

        if hasattr(self, capacity):
            async for user in getattr(self, capacity)():
                if who == user:
                    return True

            return False

    async def is_pi(self, who:Person) -> bool:
        return await self._is_involved(who, "pi")

    async def is_owner(self, who:Person) -> bool:
        return await self._is_involved(who, "owners")

    async def is_member(self, who:Person) -> bool:
        return await self._is_involved(who, "members")


class Registry(BaseRegistry):
    """ Human Genetics Programme registry """
    async def __updator__(self) -> None:
        """
        (Re)seed the registry with groups from the Human Genetics
        Programme and all user accounts
        """
        log("Updating registry", Level.Debug)
        for cls in Person, Group:
            await self.seed(cls)

    async def __serialisable__(self) -> T.Any:
        groups = []
        for gid in self.keys(Group):
            group = await self.get(Group, gid)
            groups.append(Group.href(group, rel="group", value=group.name))

        people = []
        for uid in self.keys(Person):
            person = await self.get(Person, uid)
            people.append(Person.href(person, rel="person", value=person.name))

        return {"last_updated": self.last_updated, "groups": groups, "people": people}
