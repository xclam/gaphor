"""
Unnit tests for AssociationItem.
"""

from gaphor.tests import TestCase
from gaphor import UML
from gaphor.diagram.items import AssociationItem, ClassItem, InterfaceItem, \
    UseCaseItem, ActorItem


class AssociationItemTestCase(TestCase):
    def setUp(self):
        super(AssociationItemTestCase, self).setUp()
        self.assoc = self.create(AssociationItem)
        self.class1 = self.create(ClassItem, UML.Class)
        self.class2 = self.create(ClassItem, UML.Class)


    def test_create(self):
        """Test association creation and its basic properties
        """
        self.connect(self.assoc, self.assoc.head, self.class1)
        self.connect(self.assoc, self.assoc.tail, self.class2)

        self.assertTrue(isinstance(self.assoc.subject, UML.Association))
        self.assertTrue(self.assoc.head_end.subject is not None)
        self.assertTrue(self.assoc.tail_end.subject is not None)

        self.assertFalse(self.assoc.show_direction)

        self.assoc.show_direction = True
        self.assertTrue(self.assoc.show_direction)


    def test_invert_direction(self):
        """Test association direction inverting
        """
        self.connect(self.assoc, self.assoc.head, self.class1)
        self.connect(self.assoc, self.assoc.tail, self.class2)

        head_subject = self.assoc.subject.memberEnd[0]
        tail_subject = self.assoc.subject.memberEnd[1]

        self.assoc.invert_direction()

        self.assertTrue(head_subject is self.assoc.subject.memberEnd[1])
        self.assertTrue(tail_subject is self.assoc.subject.memberEnd[0])


    def test_navigability_at_class(self):
        """Test association end navigability connected to a class"""
        c1 = self.create(ClassItem, UML.Class)
        c2 = self.create(ClassItem, UML.Class)
        a = self.create(AssociationItem)

        adapter = component.queryMultiAdapter((c1, a), IConnect)
        assert adapter
        adapter.connect(a.head)
        assert a.head.connected_to

        adapter = component.queryMultiAdapter((c2, a), IConnect)
        adapter.connect(a.tail)
        assert a.tail.connected_to

        head = a._head_end

        head.navigability = True
        assert head.subject.class_ == c2.subject
        assert head.subject.owningAssociation is None

        head.navigability = False
        assert head.subject.class_ is None
        assert head.subject.owningAssociation == a.subject

        head.navigability = None
        assert head.subject.class_ is None
        assert head.subject.owningAssociation is None


    def test_navigability_at_interface(self):
        """Test association end navigability connected to an interface"""
        c1 = self.create(InterfaceItem, UML.Interface)
        c2 = self.create(InterfaceItem, UML.Interface)

        a = self.create(AssociationItem)

        adapter = component.queryMultiAdapter((c1, a), IConnect)
        assert adapter
        adapter.connect(a.head)
        assert a.head.connected_to

        adapter = component.queryMultiAdapter((c2, a), IConnect)
        adapter.connect(a.tail)
        assert a.tail.connected_to

        head = a._head_end

        head.navigability = True
        assert head.subject.interface_ == c2.subject
        assert head.subject.owningAssociation is None

        head.navigability = False
        assert head.subject.interface_ is None
        assert head.subject.owningAssociation == a.subject

        head.navigability = None
        assert head.subject.interface_ is None
        assert head.subject.owningAssociation is None


    def test_navigability_at_usecase(self):
        """Test association end navigability connected to an usecase"""
        c1 = self.create(UseCaseItem, UML.UseCase)
        c2 = self.create(UseCaseItem, UML.UseCase)

        a = self.create(AssociationItem)

        adapter = component.queryMultiAdapter((c1, a), IConnect)
        assert adapter
        adapter.connect(a.head)
        assert a.head.connected_to

        adapter = component.queryMultiAdapter((c2, a), IConnect)
        adapter.connect(a.tail)
        assert a.tail.connected_to

        head = a._head_end

        head.navigability = True
        assert head.subject.classifier == c2.subject
        assert head.subject.owningAssociation is None

        head.navigability = False
        assert head.subject.classifier is None
        assert head.subject.owningAssociation == a.subject

        head.navigability = None
        assert head.subject.classifier is None
        assert head.subject.owningAssociation is None


    def test_navigability_at_actor(self):
        """Test association end navigability connected to an actor"""
        c1 = self.create(ActorItem, UML.Actor)
        c2 = self.create(ActorItem, UML.Actor)

        a = self.create(AssociationItem)

        adapter = component.queryMultiAdapter((c1, a), IConnect)
        assert adapter
        adapter.connect(a.head)
        assert a.head.connected_to

        adapter = component.queryMultiAdapter((c2, a), IConnect)
        adapter.connect(a.tail)
        assert a.tail.connected_to

        head = a._head_end

        head.navigability = True
        assert head.subject.classifier == c2.subject
        assert head.subject.owningAssociation is None

        head.navigability = False
        assert head.subject.classifier is None
        assert head.subject.owningAssociation == a.subject

        head.navigability = None
        assert head.subject.classifier is None
        assert head.subject.owningAssociation is None



# vim:sw=4:et:ai
